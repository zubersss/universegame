# MERIDIAN — The Quiet System

A browser-based 3D exploration game: fly an original survey ship between two
planets and a moon, land, walk, scan the strange flora and minerals, carry a
sample to each world's survey relay, and transmit the completed survey.

Built with TypeScript, Vite, Three.js (WebGL 2) and Rapier physics. All art and
sound are procedural; nothing is downloaded at runtime.

## Play

Requirements: Node.js 22.12 or newer (`.nvmrc` pins 22.22.0) and a desktop
browser with WebGL 2, keyboard and mouse. It was developed and tested in
Chromium; Firefox and Safari implement the same APIs but were not available for
testing here.

```bash
npm ci
```

```bash
npm run build
```

```bash
npm run preview
```

Open <http://localhost:4173/>. The `dist/` folder is a static site that can be
served from any ordinary HTTPS host (relative paths; worker and WebAssembly are
bundled). `vite preview` is for local use only. Opening `index.html` directly
from disk is not supported.

If the menu is slow to appear on a weak machine, open `/?preset=low`.

## Controls

| Context | Keys |
| --- | --- |
| Ship | Mouse: pitch/yaw · W/S throttle · A/D yaw · Q/E roll · Space/Ctrl up/down · Shift boost · X brake · L landing assist · G cruise · T transmit survey |
| Landed | Space take off · E exit |
| On foot | WASD move · mouse look · Shift sprint · Space jump · E interact (collect, relay, board) · hold F scan |
| Anywhere | Tab navigation, journal and survey · Esc pause (save, load, settings, recover, backups) |

Arrow keys also steer the ship and walk. If pointer lock is unavailable, drag
with the mouse button held to look.

## The expedition

1. You start landed on **Ilex**. Walk to a glowing sample deposit near the relay
   mast (markers show them) and press **E**; carry it to the relay and press
   **E** again to activate it.
2. Take off, open **Tab → Navigation** (a course is set for you after each
   relay), climb clear of the atmosphere and press **G** to cruise. Cruise
   slows and hands back control automatically before the destination's
   envelope.
3. Repeat on **Vesper** and the airless moon **Cairn**.
4. Aboard the ship, press **T** to transmit the survey. Free exploration
   continues afterwards.

Scanning plants and rocks (hold **F** while aiming within ~40 m) fills the
journal. Progress autosaves after important actions and every ~30 s; Save,
Load, Export Backup and Import Backup are in the pause menu.

## Development

| Script | Purpose |
| --- | --- |
| `npm run dev` | Vite dev server (includes the test API) |
| `npm run typecheck` | TypeScript check |
| `npm test` | Unit/integration tests (Vitest, Node) |
| `npm run build` | Typecheck + production build to `dist/` (no test hooks) |
| `npm run build:test` | Same code with the test API to `dist-test/` |
| `npm run preview` | Serve `dist/` on port 4173 |
| `npm run test:e2e` | Builds both, then runs the Playwright browser journeys |

Browser tests need Playwright's Chromium once: `npx playwright install chromium`
(players never need this). The `prod` project checks the shipped `dist/`
(no test API, same-origin requests only, WebGL 2 compatibility message); the
`journey` project drives the `dist-test/` build through player inputs. The
journeys are long (up to several hours each in software rendering); run one with
`npx playwright test --project=journey e2e/journey/landing.spec.ts`. The
longest ones replace pointer lock with a no-op because headless Chromium piles
up memory while the pointer is locked (details in `PROGRESS.md`). Browser tests
use software WebGL (SwiftShader) by default; set `PW_GPU=1` to run them on the
machine's GPU, e.g. `PW_GPU=1 npx playwright test --project=journey e2e/journey/profile.spec.ts`
for the per-preset performance route.

Project notes and the acceptance evidence are in `PROGRESS.md`; screenshots are
in `evidence/`. Asset and third-party license details are in
`ASSET_LICENSES.md`.

## Verification and known limitations

`PROGRESS.md` lists every acceptance check that was actually run, with dates,
durations and the evidence files. In short: the unit suite, a clean `npm ci`
install and build, the production smoke, and browser journeys for flight, the
continuous planet, ten land/walk/board cycles, three continuous
Ilex → Vesper → Cairn → Ilex routes at full distance, the complete expedition
with reloads, and save corruption/denied storage/backup cases all pass.

Limitations of this release and of the verification:

- Tested only in headless Chromium with SwiftShader (software WebGL). No
  hardware GPU, Firefox or Safari was available, so frame rates on real
  machines are not measured. In the software renderer the game runs well
  under 1 frame per second at 1280×720 (medians 0.9–3.8 s per frame across
  presets; the game's own main-thread work is 16–46 ms per frame); the full
  table is in `PROGRESS.md`.
- Keyboard and mouse only; no touch or gamepad controls.
- Saves live in the browser's IndexedDB for this site; use Export/Import
  Backup to move progress between browsers or machines.
- Adjacent terrain collision tiles meet within about 0.1 mm, so a ray exactly
  on a tile seam can occasionally miss; the game's ground probes tolerate a
  single miss.
- No `LICENSE` file has been chosen for the project's own code and assets
  (see `ASSET_LICENSES.md`).
