# MERIDIAN — progress

## Locked decisions
- Stack: TypeScript 5.9.3 · Vite 8.3.5 · Three.js 0.186.1 (WebGLRenderer, WebGL 2, log depth) · @dimforge/rapier3d-compat 0.21.0 · simplex-noise 4.0.3 · Vitest 5.0.5 · Playwright 1.63.0 (matches preinstalled Chromium r1243). Node 22.22 (`.nvmrc`, engines >=22.12). TS 5.9 chosen over 7.x for tooling maturity (typecheck only).
- Exact versions pinned; `package-lock.json` committed. No React/ECS/event bus/DI.
- Rapier 0.21 refreshes its query BVH only inside `world.step()` (zero-dt steps are skipped). After rebasing or installing colliders that must be queried before the next step, `Physics.refreshQueries()` runs a 1 µs step with dynamic velocities zeroed then restored (verified: no displacement, KCC works immediately).
- Rendering: three layers per frame — scaled celestial background (stars/sun/proxies) → atmosphere sky pass → local scene after depth clear. Balanced/High: HalfFloat EffectComposer → bloom → OutputPass (ACES + sRGB once) → FXAA. Low: direct to canvas with context MSAA (context AA flag fixed at page load; switching Low↔other applies AA on reload).
- Pausing always releases pointer lock (synthetic/automated Escape does not).
- Test hooks (`window.__meridian`) only in dev and the separate `build:test` (dist-test/) output; never in dist/. The test autopilot drives only player inputs (keys, mouse motion), never state. Journeys draw every 16th frame (`setRenderEvery`) because SwiftShader rasterization (~250 ms/frame) otherwise slows simulation to ~0.1x; simulation rules are unchanged.
- Flight: gravity compensation is allocated before the acceleration limit (otherwise saturated forward acceleration sinks the ship); documented deviation from the literal limit((vT-v)/tau - g) form.
- Terrain: 33x33 chunks, polynomial cube warp, 2-sample apron, continuous-surface normals on borders, morph targets on the parent's fixed-diagonal triangles, 9 quantized morph material variants sharing one program, per-vertex tiling coordinates (mod 1024 m) for precision. Contact tiles (max level) render the exact collider triangles.
- Rapier clamps dynamic-body speed to 400 m/s × lengthUnit. World uses lengthUnit 5 (2,000 m/s) with the normalized contact tolerances divided by 5, so absolute tolerances stay at defaults. Found in Phase 6: the Phase 2 tests never exceeded 199 m/s; a space-cap regression test now covers 900/1,800 m/s.
- Idle grounded player holds position when a down-ray confirms walkable support (Rapier's KCC skin correction otherwise ratchets an idle capsule downhill by up to 63 mm per 3 s).
- Distant bodies: proxies are built from each body's six level-0 root chunks (generated once by a dedicated worker, also seeded into the chunk cache), shaded with the same terrain albedo GLSL, the local lights and the same scattering integral; limb shell + cloud shells with a shared cloud clock. Activate at 3.3R (held at roots), swap at 3R, coarsen beyond 3.5R, release beyond 4R (when back at roots; forced at 4.5R).
- Cruise owns the ship transform (kinematic body, double-precision system position); exact segment/sphere sweep each step; speed limited to stop short of the envelope ahead; turns that would make an envelope unstoppable are refused.
- Saves: schema 1 record + previous-good backup rotated in one IndexedDB transaction; an invalid latest record is copied to `save-corrupt` before any overwrite and never rotated into the backup. Saved settings are informational (settings persist separately).
- Tab is owned by the game input alone (opens the panel in play, closes it from the panel, normal focus order in menus). Found by the production smoke: the panel's own Tab listener closed the panel and the input listener, seeing play resume, reopened it in the same keypress. The panel also has a Close button.
- Headless-only workaround: the long journeys (landing, travel, expedition) replace `requestPointerLock` with a no-op (`stubPointerLock` in `e2e/helpers.ts`). With the real lock, headless Chromium's renderer memory grows steadily (see Phase 8 memory notes) and hour-long runs crashed. The game reads lock state only for mouse deltas and the autopilot injects look input directly, so the journeys are otherwise unchanged; the production smoke and the shorter specs keep the real lock.
- Audio parameters glide by direct per-frame assignment, not `setTargetAtTime` (each call queued an automation event; at 60 Hz the timelines grew without bound).
- `__meridianBooted` (boot-complete flag used by the browser tests) exists only in dev/testhooks builds, like the test API.
- Profiling records raw frame intervals; only the simulation step is clamped (250 ms). A first profile attempt was discarded because the recorder stored the clamped step, so every slow software-rendered frame read exactly 250 ms.

## Current milestone
Release candidate complete (Phases 1–8 checked as recorded below). Remaining items are environment limits, not open work: hardware-GPU performance, Firefox/Safari.

## Completed acceptance checks
- Phase 1 (2026-10-29): typecheck + build pass; dev (5173) and preview (4173) render nonblank 3D; Play → HUD; Esc → pause; resize 1280×720→900×600 keeps canvas sized; emulated tab hide → pause + lock released → resume; 0 console errors/warnings, 0 failed requests. Evidence: `evidence/phase1-*.png`.

- Phase 2 (2026-10-29): Vitest: identical trajectories at 30/60/144 Hz and jittered frames (tolerance 1e-6 m), no catch-up after 60 s gap, altitude held while accelerating, brake-to-hover, 3-min random-input soak with ground strikes (max 199 m/s, min center clearance 1.13 m, no NaN). Browser (testhooks build, real keyboard events): acceleration, pitch, yaw, roll, climb >1,150 m, boost to 400 m/s, brake, hover, powered descent to rest on gear (2.8 m), pause freezes sim, input after resume; 0 console errors. Evidence: `evidence/phase2-*.png`.
- Phase 3 (2026-10-29): Vitest: exact shared directions on all 12 cube edges + 8 corners; cross-face chunk vertices/normals agree; generation identical regardless of job order; heights bounded; deterministic sites; quadtree under delayed (≤4 ticks) + shuffled worker results with a mid-run token switch keeps full coverage, no overlap and 2:1 balance at every one of 900 iterations; horizon culling conservative (4000 random cases); rebasing: 0.000 mm position error, unchanged velocities, raycast immediately after rebase hits the same point within 0.032 mm. Browser journey: face 5→0 crossing, climb to 10.7 km and back to 273 m, 271 samples with 0 coverage failures, min clearance 40 m, 28 rebases, ≤23 colliders, 1,017 chunks / 0 errors, 0 console errors. Evidence: `evidence/phase3-return-low.png`.
- Phase 4 (2026-10-29, `e2e/journey/landing.spec.ts`, testhooks build, Low, inputs only, pointer lock stubbed): passed in 37.2 min. Steep site rejected by the landing assist ("Surface too steep (23° > 12°)", ship stays PILOTING); then 10/10 cycles of assisted landing on surveyed flat sites → exit with E → walk ~25 m with a jump → stand → walk back → board with E → take off with Space. Counters 10 landings / 10 exits / 10 boardings / 11 take-offs / 0 recoveries; landing slope ≤ 12° every time; worst feet-to-mesh contact gap 2.4 cm; render mesh vs physics ≤ 0.04 mm; standing drift 0.0 mm over 3 s from rest at every site; one floating-origin rebase during the run; 0 console errors. Evidence: `evidence/phase4-after-cycles.png`. (An earlier run on the previous test build completed 9 cycles before its renderer was OOM-killed because of a concurrent diagnostic probe; see Phase 8 notes.)
- Phase 5 (2026-10-29, visual review — a judgement from screenshots, not an automated measure): before/after sets for Ilex at Balanced and Low (ground, low flight, orbit; `evidence/phase5-before-*`, `phase5-after-*`) — chalk ridges, ochre ground and dark-teal lantern groves read at ground level, the atmosphere limb and cloud shells from orbit, grove density and colours fixed (trunks no longer black, fan shrubs no longer black, loam no longer near-black), prop triangle count brought down after an early version reached ~390k triangles. Vesper (rust and pale dunes, mesas, black glass outcrops, pale dusty sky) and Cairn (black starry sky, silver rock, blue ice; numerically airless in the Phase 6 gate) are shown in `phase6-*-landed.png` and `phase7-*-landed.png`. Low keeps the same art direction (no post-processing, fewer props, shorter ranges).
- Phase 6 (2026-10-29, `e2e/journey/travel.spec.ts`, testhooks build, Low, inputs only, pointer lock stubbed): passed in 60.0 min. Three continuous rounds Ilex → Vesper → Cairn → Ilex at production distances (9 legs, 164–195 s simulated each), every leg ending LANDED on the destination's landing site with slope ≤ 12°. Cruise: 19 engagements; exits 9 automatic approach (before the envelope), 9 toggle, 1 brake-cancel (round 1, 35% of the way); 0 safety stops and 0 safety-sphere crossings; 0 recoveries. Handoff: 10 activations, 9 releases, all released at root LOD. Cairn: no atmosphere, no cloud shells, every sky colour component < 0.05. Return visits: generator heights and every prop instance within 250 m (ID and position to the mm) identical to the first visit; collision heights identical wherever both visits had colliders. Resources per leg stayed flat across rounds (geometries 193–225, textures 12, rigid bodies 7–14, colliders 10–17, chunk cache 20–27 MB, JS heap 32–51 MB); 0 console errors. Evidence: `evidence/phase6-vesper-landed.png`, `evidence/phase6-cairn-landed.png` (taken before the compact-HUD layout fix).
- Phase 7 (2026-10-29, `e2e/journey/expedition.spec.ts`, testhooks build of the final game code except the last two HUD presentation tweaks, Low, pointer lock stubbed): passed in 28.7 min. Real Play click → Ilex: walk to a deposit, E collects (inventory 1; a second E changes nothing), walk to the relay, E activates it (sample consumed; a second E changes nothing), hold F scans the relay and the nearest natural object (journal entries), board; course to Vesper set automatically. Save via pause menu → page reload → Continue: LANDED on Ilex with the same relays and species. Travel to Vesper at production distance; collect (autosave) → reload mid-walk → Continue: ON_FOOT on Vesper within 3 m of the saved spot, sample still carried; relay + scan + board. Take off toward Cairn, save in flight at > 2.5 km clearance → reload → Continue: PILOTING within 200 m and 60 m/s of the saved state; continue to Cairn, land, survey. Aboard: T transmits once (a second T does nothing), take-off afterwards works (free play), 0 recoveries, 0 console errors. Evidence: `evidence/phase7-ilex-start.png`, `phase7-vesper-landed.png`, `phase7-cairn-landed.png`, `phase7-transmitted.png`.
- Phase 7 save robustness: see "Release checks" below (4/4).

## Phase 8 notes (memory, environment)
- Real leak fixed: per-frame `setTargetAtTime` on audio parameters queued automation events without bound (renderer reached 2.6 GB and crashed in an hour-long journey). Replaced by direct smoothed assignment.
- Headless pointer lock (not a leak): with the real lock, headless Chromium's renderer accumulates collectable Blink-heap garbage quickly. Production build, real Play click, on foot, every frame drawn, 12 min: renderer RSS 0.65–0.91 GB between collections, but a forced full GC returned it to 506 / 468 / 453 / 455 MB at minutes 3 / 6 / 9 / 12 (Blink heap 33–112 MB after GC, peaks up to 491 MB). Same run without the lock: RSS ~210 MB and Blink heap ~1 MB throughout. The game reads lock state only for mouse deltas; the long journeys therefore stub the lock (decisions above).
- Incident: a diagnostic probe (production build, real lock, extra page listeners for `pointerrawupdate`/mouse/pointer events) grew its renderer to 5.9 GB in 6 minutes of loading; the container's OOM killer then also killed the concurrent landing gate (at cycle 9 of 10), which was rerun. The same flow without those listeners peaked below 1 GB. Probes are no longer run alongside gates.
- Terrain collision seams: adjacent tile colliders have separate f32 transforms and meet within ~0.1 mm. A ray exactly on a seam can pass between them (reproduced in Node: Vesper's landing site lies exactly on a chunk boundary, grid u = 8192; a ray 1 mm off the site missed). Gameplay rays tolerate a rare single miss (landing assist re-probes next step, exit-spot search tries the next spot, a restored player falls back beside the ship). The travel gate's fingerprint probe sat exactly on that seam and never completed; probes are now offset from the exact site.

## Release checks run 2026-10-29 (this environment)
- Build provenance: the journeys ran on test builds made during the day as fixes landed. Between those builds and the final source only HUD presentation changed (compact-layout location header, marker label placement and layering under panels, ship/destination marker visibility); game logic, physics, terrain, saves and the test API are the same. The production smoke and the profile ran on the final builds.
- Unit/integration: `npm test` 63/63 in 8 files (flight 6, terrain 10, rebase 1, walk 2, cruise 9, expedition 6, save 25, adaptive 4); `npm run typecheck` clean.
- Clean install: fresh copy of the tracked files → `npm ci` (53 packages, 9 s) → `npm run build` → `vitest run` 63/63. Node 22.22.0.
- Production build: no test-API strings in `dist/` (`__meridian`, `autopilot`, `setRenderEvery`, `installTestHooks` absent); the only URLs in the bundle are XML namespace / citation strings, none fetched.
- Phase 7 save specs (`e2e/journey/saves.spec.ts`, real pointer lock, Low): 4/4 passed in 8.2 min — corrupt latest record → Continue hidden, Load Previous offered, record preserved in `save-corrupt`; IndexedDB denied → title says storage unavailable, game playable (take-off), Save reports unavailable, Export downloads a schema-1 PILOTING record, Import restores flight; backup carried into a fresh browser profile (invalid file rejected first, then ON_FOOT with the collected sample restored and persisted); settings persist across reload.
- Regression journeys: Phase 3 planet journey (`planet.spec.ts`: cube-face crossing, climb out of the atmosphere and back) passed in 33.0 min; Phase 2 flight test (`flight.spec.ts`, real keyboard events) passed in 5.7 min — hover at 244.6 m altitude, full throttle to 118 m/s with altitude held within 2.9 m (ground clearance changed 59.7 → 69.7 m with the terrain), pitch climb, yaw/roll, climb past 1,150 m, boost to 422 m/s (> 350 cap), brake to 1.2 m/s, hover drift 0.5 m, descent into the ground ending at rest on the gear (2.9 m, settled as LANDED), pause freezes simulated time, resume → take off → throttle 1.0 at 98 m/s. The spec now starts from the landed state, so its altitude-hold checks use altitude above the datum (they used ground clearance when the test spawned airborne over flat ground; the first rerun failed on that by 10.9 m of terrain change) and it takes off again after the ground-contact step before testing throttle.
- Production smoke (`e2e/prod/smoke.spec.ts`, final `dist/`, idle machine): passed (59.7 s on the final rerun) — no test API, real Play click, HUD shows Landed with the location in the instrument header at 800×450, non-blank canvas, take-off with Space, Tab opens navigation, 1–3 select, Tab closes, reopen and close with the button, Esc pauses, Resume, resize to 1024×576 keeps the canvas sized, no request to test files, every request same-origin, 0 console errors. Evidence: `evidence/phase8-prod-smoke.png`.
- No-WebGL: production build in Chromium launched with WebGL disabled shows "WebGL 2 is required" with retry and no menu (`e2e/prod/nowebgl.spec.ts`, `evidence/phase8-no-webgl2.png`).

## Measured performance (this environment only)
Profile route (`e2e/journey/profile.spec.ts`, final test build, fixed seed, adaptive quality off, 1280×720, DPR 1, real Play click; every frame drawn during each 30-frame window). Browser: HeadlessChrome 153 on Linux, 4 cores; WebGL renderer "ANGLE (Google, Vulkan 1.3.0 (SwiftShader Device (Subzero)), SwiftShader driver)" — software rasterization on the CPU, so frame intervals mostly measure SwiftShader, not the game. "Main thread" is the game's own per-frame CPU time (simulation, terrain/props updates, HUD and render submission) and includes up to 4 catch-up simulation steps because frames are slow. GPU memory is an estimate from the live buffers, textures and render targets. 0 console errors in all three runs. Raw data and screenshots: `evidence/perf-<preset>.json`, `evidence/perf-<preset>-<sample>.png`.

| Preset | Sample | Frame interval median / p95 (ms) | Main thread / render submit (ms) | Draw calls | Triangles | Terrain chunks | GPU est. | JS heap |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Low | landed | 1,300 / 2,550 | 35.7 / 16.3 | 149 | 327k | 186 | 73 MB | 26 MB |
| Low | walking | 2,667 / 4,517 | 19.5 / 7.7 | 149 | 341k | 228 | 77 MB | 26 MB |
| Low | low flight | 2,533 / 5,283 | 22.1 / 9.9 | 121 | 293k | 225 | 76 MB | 26 MB |
| Low | atmosphere edge | 867 / 5,850 | 15.6 / 7.0 | 25 | 55k | 84 | 65 MB | 26 MB |
| Balanced | landed | 2,633 / 4,167 | 46.1 / 24.4 | 169 | 392k | 180 | 104 MB | 28 MB |
| Balanced | walking | 3,500 / 6,500 | 36.4 / 15.2 | 167 | 496k | 228 | 107 MB | 28 MB |
| Balanced | low flight | 3,250 / 5,916 | 34.9 / 13.7 | 140 | 434k | 225 | 107 MB | 28 MB |
| Balanced | atmosphere edge | 1,400 / 8,000 | 20.2 / 7.3 | 41 | 71k | 99 | 97 MB | 28 MB |
| High | landed | 2,217 / 4,617 | 34.2 / 18.4 | 211 | 491k | 216 | 106 MB | 38 MB |
| High | walking | 3,833 / 7,367 | 39.5 / 17.6 | 185 | 556k | 246 | 109 MB | 38 MB |
| High | low flight | 3,717 / 8,166 | 35.6 / 12.7 | 142 | 584k | 246 | 109 MB | 38 MB |
| High | atmosphere edge | 1,567 / 9,650 | 22.4 / 5.4 | 41 | 71k | 189 | 104 MB | 38 MB |

In this container the game runs at well under 1 frame per second at 720p, so the 60/30 fps targets could not be demonstrated; hardware-GPU frame rates are unmeasured. Adaptive quality (resolution first, then props, then distant LOD) is unit-tested but was disabled here to keep presets comparable.

## Unresolved blockers
- None. Environment: only Chromium (SwiftShader software GL) available; Firefox/Safari and hardware-GPU performance cannot be verified here.

## Next action
On a machine with a hardware GPU: run `npm run build && npm run preview`, play at each preset, and record real frame times (the profile spec works there too: `PW_GPU=1 npx playwright test --project=journey e2e/journey/profile.spec.ts` drops the SwiftShader flags; headless Chromium may still need its own GPU flags on some systems).

---

# Studio round (multi-session, see `STUDIO_PROMPT.md`)

Each section below is edited only by its owner. Director: integration log, decisions, interfaces.

## Studio: Director — decisions and integration log
- 2026-10-29: studio started from `main` @ `0cf5a22`. Integration branch `studio/integration`; role branches `studio/lumen`, `studio/atlas`, `studio/biome`, `studio/echo`, `studio/gauge`.
- Decision D-001: the core survey (Ilex, Vesper, Cairn relays → transmit) stays unchanged; new worlds form an Extended Survey (ATLAS proposal pending).
- Roster: LUMEN `session_01R5BrhzG9dye6xqRLrRSEkn`, ATLAS `session_01R5Bri2WGFr4gjv7TfXEPvf`, BIOME `session_01R5Bri4PYFhAo9iBZssWxCF`, ECHO `session_01R5BrhzyPMmwJkDeXRj3MPK`, GAUGE `session_01R5Bri3TS7s5DeeiUDPAdFQ`; Director `session_01R5Bri1vhfDV4bpYkM3ayeh`.
- Decision D-002: only the Director merges into `studio/integration`; roles merge integration into their branch after each announcement.
- Decision D-003: hot shared files need CLAIM/RELEASE; no acknowledgement within ~20 min → work on something else.
- M1 assignments sent: GAUGE baseline + BUGS.md + quick journey + N-body test layer; ATLAS body skeleton (Orrin, Saro) + N-body plumbing + save schema 2 + Extended Survey scaffold; BIOME fauna system + first Ilex creature + species plan; ECHO mix buses + voice pool + soak + ambience profile + airless suit mode; LUMEN baseline photo set + terrain surface quality.
- Merge 1 (`93da7c8`): `studio/gauge` @ `9ef2749`: BUGS.md, quick journey, N-body test hooks (`bodies()`, `fingerprint(body)`), `travelRoute()`. Director verification on the merged tree: typecheck clean; 69/69 unit tests; both builds; `dist/` free of test strings; quick journey passed in 1.1 min. GAUGE's generalised travel spec is still under its own 60-min verification run.

## Studio: Interfaces (agreed APIs between roles)
- **ATLAS → all: bodies (M1).** `BodyId = 'ilex' | 'vesper' | 'cairn' | 'orrin' | 'saro'`; `BODY_IDS` in that order (navigation keys 1…5; append-only, never reorder). `CORE_BODY_IDS` = ilex, vesper, cairn; `EXTENDED_BODY_IDS` = orrin, saro. New `BodyDef` field `survey: 'core' | 'extended'`; otherwise `BodyDef` is unchanged, so look/ambience keys off the existing `palette`, `atmosphere`, `clouds`, `biomeNames`, `kind` data. `isBodyId` accepts every id in `BODY_IDS`.
  | Body | Kind | Centre (m) | Radius | Atmosphere | g | maxHeight | Biome A (0) / B (1) | `special` / `rockiness` |
  |---|---|---|---|---|---|---|---|---|
  | Orrin | planet | (−720000, 240000, 600000) | 52 km | 9 km, dense, humid low haze | 9 | 650 | Basalt Column Highlands / Violet Moss Lowlands | valley floors (fog, wet) / basalt |
  | Saro | planet | (300000, −150000, −950000) | 38 km | 4 km, thin, bright | 5 | 200 | Rose Salt Flats / Brine Pan Shallows | open brine / salt domes |
- **ATLAS → all: expedition and saves (M1).** Save schema 2; `ExpeditionState.extendedTransmitted: boolean`; `inventory` is `Record<BodyId, number>` over all bodies. Object ids stay `${body}:…`, species ids `${body}-name`. `Expedition.transmit()` / `canTransmit` = core survey (unchanged rules); `Expedition.transmitExtended()` / `canTransmitExtended` = Extended Survey (core transmitted + every extended relay); `relaysActive('core' | 'extended')`. Game notices: "Survey transmitted", "Extended Survey transmitted". `ExpeditionState.discovered: Record<speciesId, simTime s>` (BIOME fills it; optional on load, keys must be logged species); species list cap 96; species and object ids are validated by pattern only (no known-list check), so fauna ids in the `${body}-name` form validate.
- **ATLAS → LUMEN: `BodyDef.look?: Partial<TerrainLook>`** (exported from `bodies.ts`): specialRough, specialSheen, bump, strata, strataSpacing (m), macro, sediment (sRGB hex), sedimentAmount, peakRock, rockSlope [start, end] as 1−cos. Unset on every body until LUMEN proposes values. **Concavity:** `chunkGen.ts` writes the signed height Laplacian ÷ grid spacing (×508, clamped ±127; + = hollow) into `morphNormal.w`; geometry unchanged (hash-locked in `tests/worlds.test.ts`).
- **ATLAS → ECHO: `BodyDef.ambience?: AmbienceDef`** (exported from `bodies.ts`): wind, windTone (Hz), windAltitude (m), tonic (Hz), scale (semitones), timbre, toneGap (s), ground. Filled for all five bodies with ECHO's values.
- **GAUGE → all: test hooks and determinism (2026-10-29).** `window.__meridian` (dev + `build:test` only) works for any body in `BODY_IDS`: `bodies()` lists every body (id, name, kind, radius, airless, landing-site direction) so specs never hard-code the list; the autopilot `travel` goal accepts any `BodyId` and throws on an unknown id; `fingerprint(body?)` returns null unless that body is shown. Request new hooks or autopilot goals from GAUGE with a `REQUEST` (what to read or drive, which spec needs it).
- **Rule: moving things (creatures, anything animated in position) must never be added to `PropSystem`.** `PropSystem` is the deterministic, static placement that the travel gate fingerprints (every instance's ID and position within 250 m of a landing site, to the mm, identical on every visit), and `nearbyScannables()` reads it too. Creatures live in their own system (`src/fauna/`, BIOME); GAUGE adds separate hooks for them (e.g. nearest creature) when BIOME's API exists.

## Studio: LUMEN (graphics)
_Not started._

## Studio: ATLAS (worlds and travel)

### M1 body skeleton (2026-10-29)
- **Two new landable planets**, Orrin and Saro (table in Interfaces). Placement validated against every body: all centre separations ≥ 554 km, safety spheres ≥ 448 km apart, every straight body-to-body line clears third bodies' safety spheres (smallest: Vesper–Orrin passes Ilex's sphere by ~47 km; this is why Orrin moved from the proposed (−700, 80, 650) km, whose Vesper–Orrin line cut Ilex's sphere by 12 km). Cruise legs from Ilex (unit-simulated with the real `CruiseController`) are within 0.8–1.25× of Ilex → Vesper. Sites: Orrin on the moss lowlands, sun elevation 23°; Saro on the salt flats at a brine-pan edge, sun 30°; both facing the approach from Ilex.
- **Generators** (`surface.ts`, first recipes, character comes in M2): Orrin = warped lowland swells cut by sinuous valleys, stepped basalt highlands broken into 30 m polygonal column cells (each raised by its own hash). Saro = an almost flat crust with shallow brine-pan basins (6 m deep), scattered low salt domes and 2 m polygonal pressure ridges along 3D Voronoi cell edges (260 m cells). Existing generators untouched (only new `case`s; per-cell salt is a new field).
- **Seams:** new bodies' landing, relay and sample sites are nudged ≥ 2 m off contact-tile seams (`seamDistance`, `avoidSeams` site preference). The original three bodies keep their released sites exactly (Vesper's known seam site included) because moving them would change their worlds.
- **Expedition (D-001):** core survey unchanged (Ilex, Vesper, Cairn → T). Extended Survey: Orrin and Saro relays, then a second T aboard ("Extended Survey transmitted"), only after the core survey. Objectives guide to the new worlds after the core transmission; the course is set automatically. Idempotent like every other step.
- **Saves:** schema 2 with migration from schema 1 on load/import (inventory zero-filled for the new bodies, `extendedTransmitted: false`, all other progress kept). A schema-1 record that mentions a new body is rejected (it cannot be genuine). A valid schema-1 latest record still rotates into the backup slot on the next write.
- **N-body plumbing:** navigation rows and keys 1…N (`Digit1–9` handler), nav status "Extended survey" for the new worlds, survey tab grouped core / Extended Survey, journal sections for every body ("No specimens catalogued yet" until BIOME adds species), inventory, objective, T prompt, title-menu save summary, sample looks (`MissionObjects` data). Proxies, handoff, cruise, gravity, autopilot already iterate `BODY_IDS`.
- **Spec changes (honest):** `tests/expedition.test.ts` "transmits once, only after all three relays" iterated `BODY_IDS`; it now activates the extended relays first (they must not enable the core transmission) and then the core ones; after the core transmission the objective is now the Extended Survey instead of "Survey transmitted". The save test fixture gained the two inventory keys and the extended flag.
- **Tests:** new `tests/worlds.test.ts` (layout, separation, line clearance, cruise legs, honest height bounds and finite data over 20,000 directions, both biomes present, day-side walkable sites off seams, original seeds/heights/sites bit-identical to the three-body release); save tests for valid v2, v1 → v2, invalid and corrupt records, export/import across schemas, store rotation with schema-1 records; expedition tests for the Extended Survey.

### M1 evidence (2026-10-29, this environment: headless Chromium, SwiftShader)
- `npm run typecheck` clean; `npm test` 125/125 in 10 files (after merging `studio/integration` @ 21c2138); `npm run build` and `npm run build:test` succeed; `dist/` has no test-hook strings.
- Browser journey (scratch spec, not committed; testhooks build of `b2d03ad`, Low, pointer lock stubbed, autopilot drives inputs only): Ilex → Orrin: leg 230 s simulated, landed on the site via the landing assist, slope 0.0°, cruise exit by approach; exit, walk to the relay, walk back, board. Orrin → Saro: leg 199 s, slope 0.0°, approach exit. Totals: 0 safety exits, 0 recoveries, 0 console errors; 16.6 min. Navigation panel lists 5 rows. Screenshots: `evidence/studio/atlas/{orrin,saro}-{approach,landed,relay}-{1280,640}.png`, `nav-panel-{1280,640}.png`.
- GAUGE quick journey (`e2e/journey/quick.spec.ts`) on the current code: passed in 1.1 min.
- `perf` hook, Ilex landed at start (one 10-frame sample, adaptive off, 1280×720; NOT the full profile route): Low 82 draw calls / 157k triangles / ≈65 MB GPU / 32 MB heap; Balanced 94 / 170k / ≈96 MB / 33 MB; High 91 / 164k / ≈96 MB / 38 MB; 5 of 5 proxies ready. All within A4. GAUGE's per-preset profile route is the authoritative check.
- Seen in screenshots: Saro reads clearly (pink crust, turquoise pans from orbit, pale sky). Orrin's moss ground renders almost black (palette too dark; M2 with LUMEN). At 640×360 the fifth navigation row is clipped at the panel's bottom edge (styles.css fix claimed, pending).
- `look` values from LUMEN set for all five bodies (the material reads them merged over its defaults; no visual change intended for the original three).

### Known limits / for other roles
- Terrain material, audio and motes still pick per-body constants with `id === 'cairn' / 'vesper'` ternaries, so Orrin and Saro currently get Ilex's defaults there (LUMEN: `terrainMaterial.ts`, `Game.ts` mote colour; ECHO: `GameAudio.ts`). The title screen text in `index.html` still names three worlds (Director's file).
- Palettes and atmosphere numbers are first-pass placeholders for LUMEN to tune.

### TODO (M2, highest impact first)
1. Orrin and Saro terrain character (organ-pipe columns at readable scale, fog valleys data, crack polygons, brine pans), with LUMEN.
2. Atmosphere/cloud data with LUMEN; distinct skies.
3. Navigation polish (arrival notice, compact layout check with five rows).
4. Optional backdrop giant (with LUMEN).

## Studio: BIOME (life and discovery)

### TODO (highest impact first)
1. M1 wiring merged + browser evidence (this section, below).
2. M2: fauna on Vesper/Orrin/Saro, Cairn phenomena, 4th flora/mineral per body (plan below; Orrin/Saro after ATLAS's merge).
3. M2: journal per-world sections with silhouettes ("??? · 1 of 4 flora found"), discovery dates (needs a save field from ATLAS), per-world completion.
4. M3: first-discovery notice + ECHO `audio.discovery(...)` + LUMEN effect hooks; fauna sound events wired to ECHO's `audio.creature(...)`.

### M1 — fauna system skeleton (2026-10-29)
- **Module `src/fauna/`** (separate from `PropSystem`; creatures are not in the prop list, so the travel fingerprint is unaffected):
  - `spawn.ts`: herds per spawn cell = cube chunk at `maxLevel − 3` (≈736 m on Ilex). Candidate hash = (body seed, `'fauna'`, **species id**, face, x, y, k), so appending species never moves existing herds (unit-tested). Homes avoid the landing clearing and relay pad.
  - `behaviour.ts`: pure state machine in each herd's home tangent plane: `idle → wander` (target inside the home radius) `→ idle`; `alert` (player within alertRadius: stop and face it); `flee` (player within fleeRadius, or ship thrusting low within shipFleeRadius; emits one `alarm`); back to `wander` after a calm period. Sub-stepped at ≤ 0.1 s.
  - `FaunaSystem.ts`: API `new FaunaSystem(def, gen, sites, aerialSteps)`, `update(dt, ctx)`, `setQuality(rangeScale)`, `nearby(point, r)`, `place(c)`, `onEvent(ev, creature)`, `dispose()`, `stats`, `triangleEstimate`. Two instanced LODs per species (caps 48 / 160 instances), procedural gait in the vertex shader from per-vertex `aLeg` (leg index, hip→foot) and per-instance `aAnim` (gait phase, walk amplitude, sway). Ground snap on the clearing-aware surface generator (the same one terrain and colliders use). Update rates: every frame < 70 m, every 4th < 200 m, every 15th to range, frozen and not drawn beyond range (380 m × preset prop range: Low 266, Balanced 380, High 494 m). No per-frame allocations in `update`/`fill`.
  - `catalog.ts`: one journal catalog (scannable flora + minerals + fauna with `kind`), used by `Journal.ts` and `Expedition.scan()`.
- **Scanning moving targets** (`src/game/scan.ts`, `stepScanTrack`): the tracked creature gets a 1.6× wider aim radius; when it slips out of the cone (or another object crosses it) progress **pauses for up to 1.5 s** instead of resetting, then resets; releasing F resets; one completion per hold. Feedback prompt: "· out of scan range" (target up to 1.5× scan range) / "· line of sight blocked", and "signal lost" with the paused bar.
- **Game.ts wiring** (claimed/acknowledged): fauna created in `showBody`, disposed in `releaseBody`, updated after the active body each frame (dt = 0 when not playing), scan target search includes `fauna.nearby()`, telemetry `fauna` stats and `scan.phase/blocked`.
- **First species: Grove trine (`ilex-trine`)** — see the plan table.

### Species plan (all five bodies)
IDs follow `${body}-name` (save schema). Existing species keep their IDs and placement hashes. "Sound" = hooks for ECHO (events `call`, `alarm`, `step` from fauna; phenomena use `call` for their periodic event).

**Ilex** — chalk ridges, ochre ground, dark-teal lantern groves
| ID | Name | Kind | Habitat | Size | Rarity | Behaviour | Sound hooks |
|---|---|---|---|---|---|---|---|
| ilex-lantern | Lantern-tree | flora | groves (existing) | 7–14 m | common | — | wind creak |
| ilex-chalk | Chalk spire | mineral | highland ridges (existing) | 2–7 m | common | — | — |
| ilex-fan | Ochre fan-shrub | flora | open ochre ground (existing) | 0.6–1.7 m | common | — | dry rustle |
| ilex-vesicle | Loam vesicle | flora | deep grove shade (special > 0.6) | 0.2–0.5 m | uncommon | bladders inflate slowly | faint wet tick |
| **ilex-trine** | **Grove trine** (M1) | fauna | grove margins, lowlands, slope < 0.25 | 1.9–2.7 m | common, herds 2–5 | grazer: wander 22 m, watch < 26 m, flee < 9 m or ship < 140 m | call: hollow chalky knock (~1/50 s idle); alarm: dry clack; step: three-beat footfalls |
| ilex-skein | Chalk skein | fauna | above highland ridges, 5–40 m up | 0.4 m span | uncommon, flocks 6–14 | flier: loose flocking along ridge updrafts, scatters upward | call: papery flutter + faint whistle; alarm: sharp flutter burst |
| ilex-sounder | Ochre sounder | fauna | open ochre flats (biome mid, low rockiness) | 0.8 m wide, flat | rare, solitary | burrower: surfaces with a ring of tendrils, sinks when footsteps come near | call: muffled thump; alarm: sand hiss on sinking |

Field notes (fauna): *Grove trine* — in the game (see `faunaSpecies.ts`). *Chalk skein* — "Thin, pale gliders no heavier than paper, riding the updrafts that rise along the chalk ridges. They move as a loose sheet, each keeping a fixed distance from its neighbours. When disturbed the sheet tears upward and reforms some way off." *Ochre sounder* — "A flattened burrower that lies just under the ochre crust, surfacing only to raise a ring of fine tendrils into the wind. It senses footsteps through the ground long before it can see anything. Most observations end with a soft collapse of sand and an empty ring."

**Vesper** — rust mesas, pale dunes, black glass outcrops
| ID | Name | Kind | Habitat | Size | Rarity | Behaviour | Sound hooks |
|---|---|---|---|---|---|---|---|
| vesper-glass | Black glass outcrop | mineral | existing | 1–3.6 m | common | — | faint ring in wind |
| vesper-pillar | Rust hoodoo | mineral | existing | 4–11 m | common | — | — |
| vesper-bristle | Dune bristle | flora | existing | 0.4–1 m | common | — | wiry hiss |
| vesper-fulgurite | Fulgurite tube | mineral | dune crests | 0.5–1.5 m | uncommon | — | — |
| vesper-sledge | Dune sledge | fauna | dune sea (biome B), lee slopes | 1.2 × 3 m, low | common, herds 3–6 | grazer: drags itself over crests on paired forelimbs; curious, approaches to ~15 m then stops; flees from the ship | call: low grinding bellow; alarm: sand-spray huff; step: long drag |
| vesper-kite | Mesa kite | fauna | above mesa edges, 20–80 m up; perches on hoodoos | 2.5 m span | uncommon, solitary | flier: circles on thermals, lands on hoodoo caps | call: thin descending whistle |
| vesper-tick | Glass tick | fauna | around black glass outcrops | 5 cm, swarms of 30–60 | common near glass | swarm: clusters on glass, ripples outward when approached, re-gathers | call: clicking like cooling glass; alarm: rising click burst |

Field notes: *Fulgurite tube* — "Hollow, branching tubes of fused sand where lightning once struck the dunes. Their inner walls are glassy and smooth; the outer surface keeps the grain of the sand that formed it." *Dune sledge* — "A broad, low grazer armoured in overlapping oxide-red plates, hauling itself over the dune crests on two heavy forelimbs. It leaves a ribbed track that the wind erases within the hour. It approaches observers to a fixed distance and waits." *Mesa kite* — "A long-winged glider that circles the mesa rims on rising heat for most of the day, descending only to rest on the caps of hoodoos. It has never been seen on the dunes." *Glass tick* — "Small crawlers with black, glassy shells, gathered in hundreds on the faces of the black glass outcrops. Disturbed, the colony spreads outward in a single ripple and slowly draws back together. Their shells are nearly indistinguishable from the mineral they live on."

**Cairn** (airless) — craters, silver rock, blue ice: no animals; phenomena instead
| ID | Name | Kind | Habitat | Size | Rarity | Behaviour | Sound hooks |
|---|---|---|---|---|---|---|---|
| cairn-rime | Rime shard | mineral | existing | 0.8–2.6 m | common | — | — |
| cairn-boulder | Silver breccia | mineral | existing | 0.8–4.2 m | common | — | — |
| cairn-bloom | Frost bloom | mineral | shaded crater walls (rime basins, steep) | 0.3–1 m | uncommon | feathery hoar that re-grows after sunlight | none (airless); suit-contact crackle when close |
| cairn-vent | Sublimation vent | phenomenon | sunlit crater floors with ice (special) | plume 3–12 m | rare | periodic silent plume of ice vapour (every 20–40 s), scannable while venting | `call` at plume start → felt as a low ground rumble through the suit (no air sound) |

Field notes: *Frost bloom* — "Feathered hoar crystals that grow on rock faces the sun never reaches. Brought into light they sublimate within minutes; returned to shadow, they rebuild in the same shapes." *Sublimation vent* — "A fissure in the crater floor that releases a silent column of ice vapour each time the ice beneath it is warmed. The plume rises straight, without wind to bend it, and falls back as fine frost around the vent."

**Orrin** (proposed; ATLAS ids `orrin`) — violet moss plains, basalt organ-pipe columns, valley fog
| ID | Name | Kind | Habitat | Size | Rarity | Behaviour | Sound hooks |
|---|---|---|---|---|---|---|---|
| orrin-moss | Violet cushion-moss | flora | moss lowlands (biome B) | 0.2–0.6 m mounds | common | — | soft damp muffling (footsteps) |
| orrin-column | Basalt organ | mineral | column highlands (rockiness) | 3–12 m clusters | common | — | wind tones across column tops |
| orrin-reed | Fog reed | flora | valley floors (special) | 2–4 m | common | sways; droplets condense | low hum in wind |
| orrin-lampcap | Lamp cap | flora | moss edges near columns | 0.3–0.8 m | uncommon | dim violet glow | — |
| orrin-wader | Fog wader | fauna | valley-floor shallows, in fog | 2.5–3.2 m, slender biped | common, loose groups 2–4 | grazer: slow, head held low in the fog; flees in long strides | call: long falling hoot; step: wet, slow footfalls; alarm: double hoot |
| orrin-drifter | Column drifter | fauna | between basalt columns, 10–30 m up | 1.5 m body + 6 m filaments | rare, solitary | floater: drifts on the air, ignores the player, rises from the ship | call: very low breathing drone |
| orrin-creeper | Moss creeper | fauna | moss plains | 0.3 m, many-legged | common, lines of 5–12 | swarm-grazer: moves in single file, freezes when approached | step: soft rustling patter; alarm: brief chitter |

Field notes: *Fog wader* — "A tall, narrow biped that feeds in the valley shallows with its head held low inside the fog layer. In clear air it appears to stand headless. It leaves in long, unhurried strides when approached and calls once before it goes." *Column drifter* — "A gas-filled body trailing long fine filaments, drifting between the basalt columns well above the ground. It shows no response to observers. Its filaments draw faint lines through the fog where they touch it." *Moss creeper* — "Small, many-legged grazers that cross the moss in single file, each following the scent of the one ahead. When one stops, the whole line stops."

**Saro** (proposed; ATLAS ids `saro`) — rose salt flats, polygon cracks, turquoise brine pans
| ID | Name | Kind | Habitat | Size | Rarity | Behaviour | Sound hooks |
|---|---|---|---|---|---|---|---|
| saro-rosette | Halite rosette | mineral | salt flats (biome A) | 0.2–0.8 m | common | — | crunch underfoot (footsteps) |
| saro-chimney | Salt chimney | mineral | brine pan margins | 1–4 m | uncommon | — | — |
| saro-mat | Brine mat | flora | brine shallows (biome B) | flat patches 1–3 m | common | — | — |
| saro-thorn | Crust thorn | flora | crack lines on the flats | 0.3–1 m | common | — | — |
| saro-skater | Brine skater | fauna | open brine (special) | 0.5 m, flat, many legs | common, groups 6–15 | skims the surface film, scatters fast | step: tiny ticking skitter; alarm: rapid skitter burst |
| saro-tilter | Crust tilter | fauna | salt flats near domes | 1.5 m, plate-backed | rare, solitary | stands for long periods angling a reflective plate to the sun; walks off slowly | call: faint metallic creak as the plate turns |
| saro-veil | Salt veil | fauna | warm brine pans, 2–15 m up | 1 cm each, columns of hundreds | uncommon | swarm: a shimmering column that leans away from the player | call: very high, faint shimmer |

Field notes: *Brine skater* — "A flat, many-legged animal that skims the surface film of the brine pans without breaking it. Groups move together and scatter in all directions at once." *Crust tilter* — "A solitary animal that stands motionless for hours, turning a broad, mirror-bright dorsal plate to follow the sun. The plate appears to regulate its temperature. It walks away when approached, slowly and without looking back." *Salt veil* — "Columns of minute translucent fliers that rise above the warm brine at midday. From a distance the column reads as a heat shimmer; only close up do individual animals resolve."

Budget plan (agreed values to confirm with GAUGE/LUMEN): ≤ 48 LOD0 + 160 LOD1 instances per species, 2 draw calls per species (+1 shadow on LOD0), ≤ 3 fauna species visible per world → ≤ 9 draw calls and a few thousand triangles for fauna in the worst case.

## Studio: ECHO (sound)

### M1 — mix architecture (2026-10-29)
- `src/audio/Mixer.ts`: buses ambience, ship, creatures, effects, ui, music (each input → level × group volume → cue duck) → master (user volume) → pause fade → glue compressor (−14 dB, 3:1) → limiter (−2 dB, 20:1, 2 ms attack) → destination. Gains change only by scheduled ramps on events (`rampTo` cancels and replaces, so a param never holds more than a couple of events); continuous layers still glide by direct assignment (A8.1).
- `src/audio/VoicePool.ts`: pooled one-shot voices, hard cap 32. At the cap the quietest voice by estimated envelope level is stolen (oldest on ties; voices still in their attack count as full level so a burst of new notes does not cannibalise itself), faded over 15 ms. Every node of a finished or stolen voice is disconnected on `onended`; a twice-a-second sweep releases voices whose `onended` never fired. Delayed cue notes (relay arpeggio, transmission chord, logged chime) are scheduled in audio time instead of `setTimeout`.
- Pause/panel/hidden tab: 80 ms fade, then `suspend()`; resume fades in over 150 ms (a resume within the fade cancels the pending suspend). First start fades in over 0.3 s. A failing AudioContext logs a console warning and the game plays silently.
- Airless suit mode (any body with `atmosphere === null`, i.e. Cairn): on foot there is no wind; a helmet hush, breathing (inhale/exhale every ~3.6–4.4 s, faster and louder after sprinting), servo whirrs on some steps, footfalls as low dull thumps through the boots, and the ship's engine reduced to a muffled trace.
- `src/audio/profiles.ts`: per-world ambience data (wind scale, wind tone, tonic, scale, timbre, tone gap, ground). Proposed as `BodyDef.ambience` to ATLAS (values for all five bodies sent); bodies without an entry use a neutral default.
- Volume settings: `music` and `effects` (0..1, defaults 0.8 / 1) beside master `volume`; old settings and save records without them sanitize to defaults. Sliders in the settings panel.
- `stats()` / `meter()` (node and voice counters; peak/RMS from an analyser on the limiter) return null unless `__TEST_HOOKS__`.
- Public API used by the game is unchanged (`start`, `update`, `footstep`, `thump`, `scanTick`, `scanDone`, `collect`, `relay`, `ui`, `complete`, `suspend`, `resume`, `setVolume`), plus `setMix`.

Tests (`tests/audio.test.ts`, mock AudioContext in `tests/audioMock.ts`): bus routing to the destination, layer/cue bus assignment, group volumes, cap never exceeded (200 voices → 32 active, 168 stolen, 0 dropped), stealing order (quietest, then oldest), steal fade (no hard cut), every voice node disconnected after a mixed burst, sweep fallback, 0 automation events on long-lived params across 20,000 varied frames, pause fade → suspend → resume, no voices while suspended, suit mode on/off, context failure, dispose, settings sanitization.

Browser soak: running, results not yet recorded (not verified).

### Sound map (event → sound → bus → visual cue)
| Event | Sound | Bus | Visual cue |
| --- | --- | --- | --- |
| Piloting / thrust / boost | two detuned saws through a lowpass that opens with thrust, thrust hiss | ship | HUD throttle and speed, exhaust plume |
| Flight through air | band-passed wind, louder and brighter with airspeed × density | ambience | speed readout, motes, sky |
| High speed in thick air | low buffeting rumble (dynamic pressure), none in vacuum | ship | speed readout, atmosphere |
| Cruise engaged / ended | rising / falling two-note chirp; cruise drone with slow beating while cruising | ui / ship | "Cruise engaged" notice, HUD mode |
| Take-off | engine spool-up | ship | HUD mode changes to flight |
| Gear up / down | motor whine, lock clunk | ship | gear state in the HUD / ship model |
| Touchdown | low sine thump + gear creak, scaled by impact speed | effects / ship | HUD "Landed" |
| Exit / board | hatch pressure hiss | effects | mode change, camera to/from player |
| Footstep | filtered noise per ground (soil, sand, rock; ice, salt, moss ready) | effects | walking motion |
| Footstep, airless | low thump + dull noise through the boots; occasional servo | effects | walking motion |
| Jump landing | small thump | effects | camera settles |
| Airless, on foot | helmet hush, breathing following exertion | ambience | black sky, airless world, HUD location |
| Scan in progress | soft blips rising in pitch with progress | effects | scan progress in the HUD |
| Scan logged | two-note chime | effects | "Journal: …" notice |
| Sample collected | bright two-tone | effects | "… collected" notice, inventory |
| Relay activated | four-note arpeggio, ambience ducked | effects | "relay active" notice, relay visuals |
| Survey transmitted | five-note chord, ambience ducked | effects | "Survey transmitted" notice |
| Extended Survey transmitted | slower six-note cue with high shimmer, ambience ducked (needs Game.ts wiring) | effects | "Extended Survey transmitted" notice |
| Ambient tones | sparse notes on the world's scale and tonic | music | none needed (decorative, carries no information) |
| Pause / panel / hidden | mix fades out, context suspended | master | pause menu / panel |

### TODO
1. Director wiring (requested): `mode` + `gear` in the audio frame, `touchdown(impact)`, `completeExtended()`.
2. Footsteps per surface under the player (needs biome/material at the foot position).
3. Creature calls with BIOME's event names; spatialized panner pool.
4. Discovery cues and sparse generative music (arrival, first discovery, transmissions).
5. Switch profiles.ts to `BodyDef.ambience` once ATLAS lands it.

## Studio: GAUGE (QA, performance, release)

### TODO (highest impact first)
1. Per-merge checks on every Director merge to `studio/integration` (typecheck, unit, both builds, `dist/` string check, prod project, quick journey, `perf` counts) → `REVIEW`.
2. Hooks/goals for the new bodies and creatures as ATLAS/BIOME APIs land (nearest creature, scan a creature, travel to each new body).
3. Extended travel gate (new worlds) and full expedition with the Extended Survey at M4; 30-min soak; per-preset profile route.

### Studio baseline (2026-10-29, `studio/gauge` = `studio/integration` @ `26538d0`, Node 22.22, 4 cores)
| Check | Result | Time |
| --- | --- | --- |
| `npm ci` | ok | — |
| `npm run typecheck` | clean | 5.0 s |
| `npm test` | 63/63 in 8 files | 26.8 s |
| `npm run build` | ok (main chunk 5,144.6 kB, gzip 1,892.3 kB) | 6.0 s |
| `npm run build:test` | ok | 2.1 s |
| `dist/` test-hook strings (`__meridian`, `autopilot`, `setRenderEvery`, `installTestHooks`) | none found (grep exit 1); present in `dist-test/` as expected | — |
| `npx playwright test --project=prod` | 2/2: no-WebGL message 1.5 s, production smoke 55.7 s | 1.1 min |

Draw calls, triangles, GPU estimate and JS heap: the studio baseline is the 2026-10-29 profile table above ("Measured performance"); same code, not rerun.

### Per-merge quick journey (`e2e/journey/quick.spec.ts`)
Testhooks build, Low, 640×360, `setRenderEvery(60)`, pointer lock stubbed. Real Play click → take off (Space) → 8 s sim of autopilot flight → assisted landing on a surveyed flat site 250–700 m away (next candidate if the assist refuses) → exit (E) → walk ~17 m → walk to the nearest scannable, aim, hold F until logged → walk to the ladder, board (E) → take off (Space). Asserts landing slope ≤ 12°, species in the journal, counters (≥ 1 landing/exit/boarding, ≥ 2 take-offs, 0 recoveries), 0 console errors. Body-agnostic (uses the starting body).
- Run 1: passed, 52.1 s (landed slope 5.1°, scanned `ilex-fan`).
- Run 2 (after the N-body hook changes, rebuilt): passed, 1.1 min (slope 0.0°, `ilex-fan`). Landing sites differ between runs because flight duration is polled in wall time against sim time; the assertions do not depend on the site.
- Run with: `npx playwright test --project=journey e2e/journey/quick.spec.ts` (after `npm run build:test`).

### N-body readiness of the test layer
- `src/debug/autopilot.ts`: route planning extracted into exported `travelRoute(from, to)` (same waypoints as before); `setGoal` rejects a `travel` goal whose `to` is not in `BODY_IDS`.
- `src/debug/testHooks.ts`: new `bodies()` hook; `fingerprint(body?)`; fingerprint documented as static `PropSystem` props only (it already read only `PropSystem`; creatures must never be added there, see Interfaces).
- `e2e/journey/travel.spec.ts`: the route is built from `bodies()` (every other body, then back to the start; identical to Ilex → Vesper → Cairn → Ilex today), airless checks apply to every airless body, counter and resource checks scale with the number of legs. New bodies therefore lengthen the gate automatically (≈ 7 min per leg at today's pace, so ≈ 20 min per added body over three rounds). Verification run of the edited spec: in progress at the time of this commit (result recorded when it finishes).
- New `tests/autopilot.test.ts`: the travel route between every ordered pair in `BODY_IDS` stays outside every safety envelope until the final radial leg, which ends inside the destination's envelope (6 cases today). `npm test` 69/69 in 9 files.
- Bugs: `BUGS.md` created; B-001 (`isBodyId` hard-codes the ids, ATLAS) filed.
