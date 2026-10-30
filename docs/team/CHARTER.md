# Lightspeed Overhaul — Team Charter

Version 2 · 2026-10-29 · Binding for the three development sessions LEAD, WORLDS and PLAYER.
Code is the truth; this charter is the agreement. Only LEAD edits it, announced with a DECISION packet.

## A. Mission

Deliver one complete playable browser game, player-facing title "Lightspeed", code in `meridian/`: pilot the ship through a navigable solar system, land on or enter a safe zone at each listed destination, leave the ship as a visible animated character, explore with that destination's power, discover and scan something worthwhile, return to the ship, travel on, save and resume. Build on the existing MERIDIAN engine. Optimize for the strongest finished experience per unit of effort.

## B. Non-negotiables

1. No wholesale rewrite. Replace a subsystem only for a demonstrated blocker or a measured benefit, recorded in `STATUS.md`.
2. No custom engine, generic ECS, plugin system, orchestration server, universal ability graph, event bus, DI container, or infrastructure for hypothetical needs (`PROGRESS.md` already locks "no React/ECS/event bus/DI").
3. Exactly three development sessions: LEAD, WORLDS, PLAYER. No fourth tester or manager, no nested developers, no agents acting outside a session. A session's subagents and workflow agents (any number) work for that session: they may research and review anything, edit only that session's owned files, and report back; none becomes a session or owns files of its own.
4. One owner per file (section D). A session changes a file it does not own only through an IFACE request to the owner. If the owning session is not running (archived or failed, or no reply within 2 h to a message naming the task), LEAD may take over that task and its files: it sends a takeover packet, works on `lead/<task>` from the owner's last pushed commit, records it in `STATUS.md`, never retries the blocked part of a task stopped on an O blocker (B.9), and hands the task back by packet when the owner replies.
5. Stack is pinned (section C). No engine or library churn once the baseline builds.
6. No repeated research into settled decisions. Settled = this charter plus the "Decided" list in `STATUS.md`.
7. No placeholder counted as done, no silent scope reduction, no hidden regressions, no fabricated test results, no claim of invisible or background progress after a session ends.
8. After two focused failed attempts at a noncritical technique, test a simpler alternative or defer it with a written reason. Critical failures (startup, movement, collision, mode handoff, save) are fixed or reported as blockers.
9. Ordinary reversible development needs no approval. Stop only for access, credentials, payment, a real permission boundary, or a decision that cannot be responsibly inferred; while one is pending, keep working on everything that does not depend on it. Never route a denied action through another session.
10. The GitHub Actions GPT bridge (`.github/`, `scripts/ai_bridge.py`) is neither used nor modified. No OpenAI API, no new paid service, no unverified automation.
11. Quality assurance belongs to all three. Each session tests its own work: before a READY, typecheck, unit tests, build, the production smoke and the specs that cover the change; journeys longer than 10 minutes run once per milestone, at the gate (LEAD runs them on the integrated build); a consequential interface change is checked by its consumer before LEAD integrates it; for an interface with no consumer code yet, LEAD integrates after its own checks and the consumer reports problems as DEFECT on first use; if the consumer session is not running or has not answered within 2 h, LEAD runs the consumer's checks itself, records them and integrates.

## C. Baseline (verified 2026-10-29, `main` at `0cf5a22`)

- Repository `zubersss/universegame`; game in `meridian/`; published build copied to `play/meridian/` for GitHub Pages.
- Stack: TypeScript 5.9.3, Vite 8.3.5, Three.js 0.186.1 (WebGL 2, log depth), @dimforge/rapier3d-compat 0.21.0, simplex-noise 4.0.3, Vitest 5.0.5, Playwright 1.63.0, Node ≥ 22.12. Versions pinned in `package.json` and `package-lock.json`.
- Commands (run inside `meridian/`): `npm ci` · `npm run dev` · `npm run typecheck` · `npm test` · `npm run build` (typecheck + `dist/`) · `npm run build:test` (`dist-test/` with test hooks) · `npm run preview` (http://localhost:4173/) · `npm run test:e2e`; browser tests need `npx playwright install chromium` once; `PW_GPU=1` runs them on the real GPU.
- Existing systems to keep: fixed-step loop (`src/core/loop.ts`), floating origin (`src/core/origin.ts`), cube-sphere terrain with worker generation, quadtree LOD and collision tiles (`src/terrain/*`), deterministic surfaces (`src/world/surface.ts`), landing assist and cruise (`src/ship/*`), saves with previous-good backup (`src/save/*`), proxies, atmosphere and clouds (`src/render/*`), props (`src/props/*`), procedural audio, settings presets with adaptive quality, test hooks and autopilot (`src/debug/*`), Playwright journeys (`e2e/*`).
- Modes: `PILOTING | CRUISING | LANDED | ON_FOOT` (`src/game/Game.ts`). Save schema 1 (`src/save/SaveSystem.ts`).
- `AGENTS.md` rules 1–12 remain in force for everyone; its "Automated GPT + Claude Code collaboration" section governs only the GitHub Actions bridge runs (unused, B.10), so its push, merge and pull-request limits do not apply to the three sessions (F).
- Legacy handoffs live in `docs/team/handoffs/`. LEAD reconciles them against this code in M1; a claim in a handoff is REPORTED until checked here.

## D. Roles and file ownership (paths under `meridian/` unless noted)

| Session | Owns | Also owns (cross-system, change by IFACE) |
|---|---|---|
| LEAD | `src/game/*`, `src/core/*`, `src/physics/*`, `src/ship/*`, `src/save/*`, `src/render/RenderSystem.ts`, `Lighting.ts`, `CameraRig.ts` (ship cameras), `Adaptive.ts`, `src/ui/Menus.ts`, `Hud.ts`, `Panel.ts`, `Markers.ts`, `styles.css`, `src/audio/GameAudio.ts`, `src/debug/*`, `src/main.ts`, `index.html`, `package.json`, `package-lock.json`, `tsconfig*`, `vite.config*`, `playwright.config.ts`, `e2e/prod/*`, `e2e/journey/{flight,travel,saves,expedition,profile}.spec.ts`, `README.md`, `PROGRESS.md`, repo-root `README.md`, `play/`, `docs/team/*` | `Mode` and mode routing, save schema, dependencies, entry point, renderer configuration, HUD slot API, `Expedition.ts` objective data format |
| WORLDS | `src/world/*` (incl. new `zones.ts`, `catalog.ts`), `src/terrain/*`, `src/props/*`, `src/render/{Atmosphere,Clouds,Space,BodyProxies,terrainTextures,Motes}.ts`, `src/data/**` (catalogs, Earth dataset), `scripts/data/*` (dataset conversion), `src/ui/Journal.ts` (body entries), `ASSET_LICENSES.md`, `e2e/journey/planet.spec.ts`, new `e2e/journey/worlds-*.spec.ts` | `BodyDef` and catalog types, `SurfaceInfo` and surface queries, `Zone` type, scale and epoch constants |
| PLAYER | `src/player/*` (incl. new `CharacterCamera.ts`), new `src/avatar/**` (model, rig, animation), new `src/abilities/**`, new `src/ui/AbilityHud.ts`, new `src/audio/abilitySounds.ts`, `e2e/journey/landing.spec.ts`, new `e2e/journey/avatar-*.spec.ts` and `powers-*.spec.ts`, `src/debug/playerHooks.ts` (PLAYER test hooks) | `AbilityConfig`, `AbilityState`, on-foot input bindings; on-foot behaviour through the ON_FOOT hooks (`src/game/onFoot.ts`: enter, step, frame, exit) installed from `src/player/install.ts` |

LEAD implements code every milestone (ship flight, travel, saves, integration, HUD, settings); coordination is a minority of its time.

## E. Communication

Messages are plain text over cross-session messaging (fallback: `docs/team/packets/<ROLE>.md` on the sender's pushed branch; each session owns its own packets file). One format:

```
[LS] from=WORLDS to=LEAD type=READY task=W-04 base=<integration commit>
changed: src/world/catalog.ts, src/data/sol.json
checks: npm test (112 pass), npm run build ok
notes: BodyDef.explore added; PLAYER must read zone bounds from Zone.floorAlt
next: LEAD merge; PLAYER adapt AbilityConfig.bodyIds
```

Types: READY (work merged to your branch and checked) · BLOCKED (what, since when, what unblocks) · IFACE (interface change proposed or landed; consumer checks before LEAD integrates) · DEFECT (repro, severity, files) · DECISION (question + your recommendation; LEAD answers promptly, choosing the smallest approach that passes the player-facing test). Send only on these events. No status chatter, no acknowledgment loops, no two sessions researching one settled question. A message carries information only: it never shares files, history, approvals or permissions.

`docs/team/STATUS.md` (LEAD-owned) holds: Effective configuration · Decided · Integration base · Task table · Blockers · Milestone gate results. Task record fields: ID · owner · player-visible outcome · dependency · integration base · owned files · contract/acceptance check · result (commit, checks run, remaining issues, next handoff). WORLDS and PLAYER update their own task rows via READY packets; LEAD writes the file. In relay mode (no messaging), each session writes its packets to `docs/team/packets/<ROLE>.md`.

## F. Git and integration

- Branches: `overhaul/integration` (LEAD only), session branches `lead/*`, `worlds/*`, `player/*`. Each session works in its own git worktree, never switches branches in another worktree, and pushes its own branch after every commit; LEAD pushes `overhaul/integration` and the `overhaul-mN` tags. Integration, takeover and the packets fallback read only pushed branches.
- Commit small, with the task ID in the message. Rebase your branch onto `overhaul/integration` at least daily; resolve conflicts inside your owned files only.
- LEAD integrates in dependency order (contracts → worlds → player → game), runs affected checks (`typecheck`, `npm test`, `build`, the relevant journey), and tags a known-good checkpoint `overhaul-mN` at each milestone gate.
- `main` changes only by pull request at a milestone gate; LEAD opens it and merges it once the gate's checks pass and are recorded in `STATUS.md` (GitHub API or connector); if a permission boundary refuses that, the pull request stays open with the gate recorded and work continues on `overhaul/integration`. `play/meridian/` is rebuilt only at release gates.
- Only LEAD touches `package.json`, the lockfile, `vite.config*`, `index.html`, `tsconfig*`.
- A stopped session's work stays on its branch; LEAD lists its unfinished tasks in `STATUS.md` and does not duplicate a task its owner is still writing; a task whose owner session is not running may be taken over (B.4).

## G. Tools, effort, permissions

- At start, each session records in `STATUS.md` (via LEAD): Claude Code version, model (`/model`), effort (`/effort status`), ultracode state, permission mode, `/list-agents` result. Report the effective configuration; a sentence in a prompt changes no runtime setting. LEAD fills what it can read from session records; a value no session can read from inside is recorded as "not readable in-session" and blocks no task or gate.
- Effort `xhigh` or `ultracode` in all three sessions; ultracode may stay on, and a session may run dynamic workflows within B.3. LEAD may raise one hard decision to `max` for that session only.
- Do not change the selected model, permission settings, billing or usage settings. If a model needs usage credits, the owner decides.
- `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS` stays unset on the primary path.
- Tools by task: terminal, source search, installed library APIs, git diffs and existing tests for implementation; Playwright or the dev server in a real browser for functional checks; browser profiling, `__meridian.perf()` and `resources()` test hooks for performance; official documentation for uncertain APIs; code-built models (and a verified CC0 asset only if licensed and recorded) for the character; official astronomical and geospatial sources for data. Nothing is assumed installed; assets are never hotlinked.
- Project settings (repo-root `.claude/settings.json`, approved by the owner 2026-10-29): `permissions.allow` = `Bash(npm *)`, `Bash(npx *)`, `Bash(git *)`, `Bash(node *)`. `crossSessionInbound` = `accept` is set per user, because a repository file may only tighten it. All three sessions run in the same permission class; never mix a bypass-permissions session with prompting ones, or messages are held.

## H. The game

Loop: start → pilot → take off → travel → approach → land or enter zone → exit as the character → explore with the power → discover/scan → return → travel → save/resume. Progression "First Light": Earth (flight) → Moon (blink) → Mars (speed), each with one guided route and three scan targets, then free exploration of everything else. Reuse `Expedition.ts` with new objective data; keep scanning, journal and markers. No survival, economy, dialogue, factions or multiplayer.

Scope (final target, staged):

| Destination | Exploration | Data basis | Power | Milestone |
|---|---|---|---|---|
| Sun | navigable, heat hazard, no landing | measured radius, luminosity | — | M2 |
| Mercury | surface (suit shields heat/cold: fictional device) | measured globals + procedural infill (labeled) | Sunline Dash | M3 |
| Venus | surface (suit shields pressure/heat: fictional) | measured globals + procedural (labeled) | Pressure Glide | M3 |
| Earth | surface, real geography | ETOPO-class elevation + land mask + coarse biome, procedural detail below data resolution | Skyborne Flight | M2 |
| Moon | surface | measured globals + large-feature placement where feasible, procedural infill (labeled) | Lunar Step (teleport) | M2 |
| Mars | surface | measured globals + large features where feasible, procedural (labeled) | Redline (superspeed) | M2 |
| Jupiter | upper-atmosphere EVA zone, no solid ground | measured globals; zone fictional | Storm Lift | M3 |
| Saturn | ring-plane platform zone | measured globals; zone fictional | Ring Skate | M3 |
| Uranus | upper-atmosphere EVA zone | measured globals; zone fictional | Cold Drift | M3 |
| Neptune | upper-atmosphere EVA zone | measured globals; zone fictional | Gale Rider | M3 |
| Europa | surface (ice) | measured globals; procedural (labeled) | Anchor Blink | M3 |
| Titan | surface, dense air, liquid lakes as hazard | measured globals; procedural (labeled) | Wing Glide | M3 |
| Asteroid belt, Kuiper belt | navigable sparse fields, lightweight instanced rocks | real radii bands | — | M3 |
| Alpha Centauri A, B, Proxima; Barnard's Star | star map with checked catalog positions and distances; jump travel | catalog, cited | — | M4 |
| Proxima b | procedural surface, labeled fictional | real planet, invented surface | Terminator Step (blink + flight) | M4 |
| Quiet System (Ilex, Vesper, Cairn) | existing content, labeled fictional, optional | fictional | existing walk | M4 if free |

Scale and data policy: scientific values live in `src/data/*.json` with `source`, `accessed`, `license` fields and are shown in the journal with a tag `measured | estimated | fictional` per field. Gameplay values derive from them by documented constants in `src/world/scale.ts`: body radius = real ÷ 40 clamped to 12–200 km; heliocentric positions = Horizons position vectors at one documented epoch (`EPOCH` constant) ÷ one documented factor chosen so Earth sits about 3,000 km from the Sun; a moon sits in its real direction from its parent at parent gameplay radius × √(real parent–moon distance at EPOCH ÷ real parent radius), and at least 4.5 × the sum of the two gameplay radii (the Moon about 1,240 km from Earth), because the single factor would put it inside its parent; bodies are static at that epoch; gravity real; travel: cruise max speed = max(15 km/s, hop distance ÷ 45 s); interstellar travel is a jump sequence of about 6 s; nothing presents compression as physical simulation. A changed gameplay seed never moves Earth's continents: real-data bodies ignore the seed for the data layer and use it only for infill. Earth data: one equirectangular elevation raster (lon −180→180 west to east, lat 90→−90 top to bottom, meters, nodata handled), one land mask, one coarse biome raster; projection, seam, pole and unit handling verified by a unit test that samples known coordinates (Everest region high, Challenger Deep low, land fraction ≈ 29%). Bundle at most 8 MB of data, lazy-loaded per body.

## I. Shared contracts (adapt the existing types; do not add an abstraction layer)

| Contract | Fields and units | Producer → consumer | Owner |
|---|---|---|---|
| `BodyDef` (`src/world/bodies.ts`, becomes catalog-driven) | `id: string` · `system: 'sol' \| 'proxima' \| 'quiet'` · `kind: 'star' \| 'planet' \| 'moon' \| 'belt'` · `explore: 'surface' \| 'zone' \| 'none'` · `real: {radiusKm, gravity, …, source}` · gameplay `center` [m, system frame], `radius` [m], `gravity` [m/s²], `atmosphereHeight`, `maxHeight`, `maxLevel`, `seed` · `surface: 'procedural' \| 'data'` + `dataset?` · `zone?: ZoneDef` · `power: AbilityId` · `fiction: string[]` (which aspects are invented) | WORLDS → everyone | WORLDS |
| Frames | system (double, m, Sun at origin) · body-local (m, body center) · physics/render local (floating origin, rebase 2,048 m) · surface frame (radial up) | LEAD conversions (`FloatingOrigin`, `ActiveBody`) | LEAD |
| `SurfaceGenerator` (`src/world/surface.ts`) | `height(nx,ny,nz)` m above datum · `info()` → `SurfaceInfo{height, biome, variation, special, rockiness, hazard 0–1, liquidLevel m \| null}` · pure, deterministic, worker-safe | WORLDS → terrain, collision, props, spawn, landing | WORLDS |
| Surface queries (`ActiveBody`) | `heightAt(dir)` · `surfaceInfo(dir)` · `groundProbe(posLocal, maxDist) → {point, normal, slopeDeg} \| null` · `collisionReady(posLocal, radius) → boolean` | WORLDS → PLAYER, ship | WORLDS |
| `ZoneDef` | `center` (body frame) · `radius` m · `floorAlt`, `ceilingAlt` m · `wind(p) → Vector3` m/s · `hazards[]` · `platforms[]` (collision meshes) | WORLDS → PLAYER | WORLDS |
| `Mode` | `PILOTING \| CRUISING \| LANDED \| ON_FOOT`; one owner of position per entity per mode (ship: `Ship`/`Cruise`; character: `Avatar` controller) | LEAD | LEAD |
| `AbilityState` (inside ON_FOOT) | `walk \| flight \| speed \| blink \| drift` + transition rules | PLAYER → HUD, saves, audio | PLAYER |
| `AbilityConfig` | `id` · `primitive: flight \| speed \| blink \| drift` · `bodyIds[]` · `controls` · `params` (m, m/s, m/s², s) · `feedback` | PLAYER → UI, saves | PLAYER |
| HUD slot API | `hud.setAbility({name, state, charge, cooldown, hint})` · `hud.setWarning(text, severity)` | LEAD provides → PLAYER, WORLDS | LEAD |
| `SaveData` schema 2 | `schema: 2` · `generator` · `seed` · `bodyId: string \| null` · `system` · `mode` · `ship` · `player` + `abilityState` · `unlocked: AbilityId[]` · `discoveries[]` · `expedition` · `settings` · `lastSafeLanding` · `navTarget`. Schema-1 record is kept as `save-legacy` and offered as read-only history; no migration of positions. `MAX_COORD` rises with the new system scale | LEAD | LEAD |
| Determinism key | `hashCombine(WORLD_SEED, GENERATOR_VERSION, bodyId, subsystem, spatialKey)` (existing pattern) | WORLDS | WORLDS |

## J. Engineering rules

- Coordinates: astronomical positions never enter mesh or physics data; everything local goes through the floating origin. Radial up for every body; character and camera orientation follow `alignUp`. Fixed step stays 60 Hz with the existing 4-step cap and 250 ms clamp; render interpolation stays; controls are identical at 30, 60 and 144 Hz (existing tests extend to abilities).
- Handoffs: ship → character placement uses `groundProbe` plus a capsule clearance test within 3 m of the hatch, else the nearest valid point within 20 m, else the landing site; the ship keeps a persistent marker; "Return to ship" is always in the pause menu; "Recover" returns to the last safe landing. Pause and loading freeze both entities. Powers deactivate only on boarding; a zone boundary pushes back softly for 3 s and then recalls to the ship. Leaving superspeed always passes through braking; flight never ends mid-air.
- Water and hazards: `liquidLevel` below the feet by more than 1.2 m triggers swim-back (fade, return to last ground within 2 s, no fluid sim); hazard regions run a visible timer and recall to the ship when it expires (fictional suit device).
- Streaming: generation keyed by seed, generator version, body, subsystem and location; worker order never changes content; bounded queues with priorities, cancellation and stale-result rejection; dispose every resource; coarse distant bodies, fine terrain around play; continuous geography across chunk and face boundaries; proxies and surface read the same generator. Late streaming limits speed and teleport range rather than stalling; constant loading pauses are a defect.
- Traversal safety: collision readiness must cover `speed × 2 s + braking distance + 50 m` in the movement direction (extend `TerrainCollision.computeWanted`); superspeed uses a swept capsule cast each step with slope and ledge rules and a braking curve; teleport commits only after range, line-of-sight, clearance (capsule cast at the target) and loaded-collision checks pass, never into unloaded or solid space; failed checks give red feedback and consume nothing.
- Persistence: save seed, versions, body and location, ship state, discoveries, ability progress and settings; sparse changes only; reload tested while landed, exploring, mid-transition and after changing destinations.
- Prefer direct modules and small data tables. Keep an existing solution that passes these rules.

## K. Character and powers

Character: an original articulated explorer in a consistent suit, built as a Three.js `SkinnedMesh` with a bone hierarchy and procedural, state-blended animation (idle, walk, run, jump, fall, land, board, exit, plus power poses). Readable silhouette, suit materials from the existing PBR path, 1.8 m tall, no foot sliding (stride tied to speed), no clipping on slopes up to the walk limit. Third-person by default (`CharacterCamera`: spring arm, terrain-avoiding, reduced-motion aware); first-person stays available with `C` if it costs nothing extra. A verified CC0 rigged glTF may replace the code model only if licensed, under 2 MB and recorded in `ASSET_LICENSES.md`.

On-foot controls: WASD move · mouse look · Shift sprint · Space jump · E interact · hold F scan · C camera · Q power (primary) · hold right mouse to aim · X brake · Esc pause. Rule: arriving at a destination unlocks its power in the journal; the power is active while exploring that body or zone and never elsewhere. No exceptions.

| Body | Power | Primitive | Controls | Initial tunables | Route that shows it |
|---|---|---|---|---|---|
| Earth | Skyborne Flight | flight | hold Space 0.6 s take off · Space/Ctrl climb/descend · W/S accelerate/decelerate · Shift boost · X brake-to-hover · descend below 1.5 m at < 4 m/s to land | accel 25 m/s², cruise 90 m/s, boost 220 m/s, climb 30 m/s, brake 60 m/s², turn 1.5 rad/s, ceiling 2,000 m above ground | coast crossing to a mountain summit beacon |
| Mars | Redline | speed | hold Q while grounded · steer with look · X or release brakes | accel 40 m/s², top 110 m/s, yaw 3→0.8 rad/s with speed, slope ≤ 35°, brake 50 m/s², lookahead speed × 2 s + 50 m | canyon run between three relays |
| Moon | Lunar Step | blink | hold right mouse: preview · Q or click: commit | range 60 m, cooldown 1.2 s, line of sight required, arrival velocity 0, target clearance = capsule cast, ground within 2 m or airborne within 3 m of ground | crevasse field crossing |
| Mercury | Sunline Dash | speed (burst) | Q = 15 m burst in 0.25 s, 3 charges | recharge 1 s per charge in shadow only; 60 s in direct sun → overheat recall | shadow-hopping along the terminator |
| Venus | Pressure Glide | flight (glide) | as flight, no powered climb above 250 m above ground | glide ratio 8:1, climb 8 m/s in marked thermals, soft ceiling | highland-to-highland glide |
| Europa | Anchor Blink | blink | as blink; long blink only to anchor points | free range 40 m, anchor range 140 m, ice friction 0.1 | chaos-terrain fissure crossing |
| Titan | Wing Glide | flight (flap) | Space flaps | +6 m/s per flap, cruise 35 m/s, ceiling 400 m, lakes = liquid hazard | lake-shore ridge flight |
| Jupiter | Storm Lift | drift | WASD bursts · ride updrafts · X dampers | bubble radius 6 km, updraft 15 m/s, lateral burst 12 m/s, floor recall | updraft chain to a lightning vista |
| Saturn | Ring Skate | drift | bursts · dampers | 8 km disc platform in the ring plane, burst 20 m/s, boulder collisions, labeled fictional | boulder slalom to a beacon |
| Uranus | Cold Drift | drift | bursts | drift 8 m/s, long bursts, crystal clouds slow movement | sideways-lit crossing |
| Neptune | Gale Rider | drift | bursts across jet bands | bands carry 60 m/s, cross-band steering, floor recall | band crossing to a vortex rim |
| Proxima b | Terminator Step | blink + flight | blink allowed in flight | day-side heat and night-side cold timers; terminator band safe | capstone route along the terminator |

Every power ships with: an exploration purpose and one route or landmark; exact controls and interaction with walking; tunables in gameplay units; visual, animation and audio feedback with readable camera; tests for collisions, transitions, save/load and low frame rate. Four primitives only (flight, speed, blink, drift); variants are parameter sets plus small rule hooks.

## L. Graphics and performance

- Reference device: the owner's Windows laptop (8 GB RAM) in current Chrome; LEAD records CPU, GPU (`chrome://gpu`) and resolution in `STATUS.md` when the owner runs it. Until then LEAD verifies behaviour in its own environment, labels any numbers with that environment (software-rendered frame times are not performance evidence), and reference-device runs do not block the M1–M4 gates. Targets, not guarantees: 60 fps at 1080p on Balanced and 30 fps at reduced resolution on Low, verified on that device; if its GPU is integrated, Low is the baseline there and Balanced is verified on the best available hardware.
- Budgets (set at M1 from the measured baseline, provisional): initial download ≤ 10 MB compressed plus ≤ 8 MB lazy data; resident terrain chunks ≤ 300 (Balanced); draw calls ≤ 400; triangles ≤ 1.2 M; generation work ≤ 8 ms per frame on the main thread; JS heap steady ≤ 400 MB; GPU estimate ≤ 350 MB; no growth across 20 travel/return cycles.
- Techniques (few, high impact, all supported by the current renderer): per-body palettes and biome materials; a liquid-surface shader for Earth and Titan; tuned cloud and atmosphere per body; the Sun as the real light with per-body direction; character and ability materials and VFX (trails, speed lines, blink flash), restrained; HUD cleanup. Not allowed: path tracing, second renderer, full fluid weather, material compiler.
- Measurement: `profile.spec.ts` on the reference device with `PW_GPU=1` (owner-run; LEAD's own runs are labeled with their environment), plus manual play; frame times during fast traversal, landing, ability use and repeated planet changes; resource counts and heap over time. A standing scene at a high average is insufficient evidence.
- Comfort: clear bindings, pause, sensitivity, reduced motion and camera shake off; spectacle never obscures aiming, terrain or landings. Nonblocking startup progress and useful failure messages.

## M. Milestones and gates

| Milestone | LEAD | WORLDS | PLAYER | Gate (observable) |
|---|---|---|---|---|
| M1 Baseline, contracts, channel | L1 `npm ci`, `npm test`, `npm run build`, `npm run preview` in LEAD's environment (reference device when available); L2 commit charter, STATUS, project settings; L3 messaging round-trip with both sessions; L4 reconcile handoffs, record disputes; L5 land catalog types, `Mode` extension, schema-2 plan, HUD slot API | W1 `src/data/sol.json` from Horizons at `EPOCH` with sources; W2 `scale.ts`; W3 Earth dataset chosen, converted, terms recorded, sampling test; W4 `SurfaceGenerator` from data (spike on a small region) | P1 code-built rigged character rendering and walking on Ilex in third person; P2 ability primitive skeleton with `walk` only; P3 avatar journey spec scaffold | All checks green in LEAD's environment; Chromium play confirmed; L3 messaging round-trip recorded (a session stopped later does not block the gate; its tasks follow B.4); STATUS.md complete; Earth sampling test passes |
| M2 First slice | L6 Sun as light source; L7 transfer travel and nav for Sun + 8 planets + Moon; L8 schema 2 saves; L9 journal unlock and "First Light" objectives; L10 integration + `travel.spec.ts` extended | W5 Earth real geography with infill, continuity orbit↔surface; W6 Mars and Moon surfaces; W7 proxies and atmospheres for all M2 bodies; W8 `groundProbe`/`collisionReady` | P4 full base animation set; P5 Skyborne Flight; P6 Redline; P7 Lunar Step; P8 power HUD/audio/VFX; P9 `powers-*.spec.ts` | Full loop Earth → Moon → Mars playable with avatar and powers; save/reload in every mode; all journeys pass; Earth recognizable from orbit and on the ground |
| M3 Solar system | L11 belts in cruise; L12 zone entry mode handling; L13 settings and HUD for hazards | W9 Mercury, Venus, Europa, Titan; W10 giant zones with wind fields and platforms; W11 belts; W12 labeling in journal | P10 remaining powers (drift primitive + variants); P11 hazard timers and recall; P12 tests | Every listed destination reachable and explorable per table; labels correct; no holes or falls in a 20-cycle journey |
| M4 Nearby stars | L14 jump travel and system switching; L15 saves across systems | W13 star catalog with citations; W14 Proxima b fictional surface; W15 optional Quiet System relocation | P13 Terminator Step; P14 capstone route | Jump to Proxima b, explore, return, reload |
| M5 Polish and delivery | L16 presets measured in LEAD's environment (labeled) and on the reference device when the owner runs it; L17 regression run; L18 ≥ 45 min soak; L19 release report; L20 build to `play/`, published by the release pull request | W16 visual pass per body within budgets | P15 animation and camera polish; P16 comfort options | Definition of done (N) met with evidence |

## N. Definition of done

Clean `npm ci` + `npm run build` + `npm run preview` in Chrome on the reference device when the owner has run it, otherwise in LEAD's environment with that limit stated · all three roles integrated in one build · full ship → surface/zone → character/power → ship loop · Earth recognizable from orbit and ground; procedural worlds stable across revisits and reloads · complete destination and power table with scientific vs fictional labels · usable character with every power including Earth flight, Mars superspeed and Moon teleport · no reproducible terrain holes, falls through collision, teleports into geometry, broken transitions or silent save loss · seam, determinism, high-speed collision and ability-boundary checks in the suite · 20 travel/return/reload cycles and a 45-minute soak without stalls or growth · screenshots from the running game plus honest frame-time tables (software-rendered tables labeled as such until reference-device tables exist) · production build, controls list, launch instructions · `play/meridian/` updated and published by the release pull request, the Pages URL confirmed to load by LEAD or, if LEAD's network cannot reach it, recorded as owner-to-confirm with a labeled local-preview run as evidence · release report in `PROGRESS.md`.

## O. Blockers

Stop and report only for: missing access or credentials, a purchase, an actual permission boundary, or a decision that cannot be inferred (title change, a paid asset). While one item is blocked, continue every task that does not depend on it.
