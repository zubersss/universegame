// Regenerates the landed-save fixtures the power journeys import
// (e2e/journey/powers-*.spec.ts): moon-landed.json and mars-landed.json.
//
// Each is a real backup exported from a run, never hand-edited: a new Sol
// expedition starts landed on Earth; the navigation panel (Tab, then the body's
// key) sets the course; the test autopilot flies there through player inputs
// only and lands; the pause menu's Export writes the backup. The Mars run
// starts from the Moon landing, as a player would travel.
//
// Run against a test build (npm run build:test, then
// npx vite preview --outDir dist-test --port 4174):
//   node e2e/fixtures/regenerate.mjs [baseURL]
// Regenerate whenever the save schema, the Sol start or the landing sites change
// (the journeys fail with "regenerate fixture" when an import no longer works).

import { chromium } from 'playwright';
import { readFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const base = process.argv[2] ?? 'http://localhost:4174/';
const here = dirname(fileURLToPath(import.meta.url));

const browser = await chromium.launch({ args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] });
const page = await browser.newPage({ viewport: { width: 960, height: 540 }, acceptDownloads: true });
const errors = [];
page.on('pageerror', (e) => errors.push(e.message));
await page.addInitScript(() => {
  Element.prototype.requestPointerLock = function () {
    return Promise.resolve();
  };
});
const snap = () => page.evaluate(() => window.__meridian.snapshot());
const until = (cond, timeout) => page.waitForFunction(`(() => { const s = window.__meridian.snapshot(); return ${cond}; })()`, null, { timeout, polling: 500 });

await page.goto(new URL('?preset=low&system=sol', base).toString());
await page.waitForFunction(() => window.__meridianBooted === true, null, { timeout: 300_000 });
await page.evaluate(() => window.__meridian.setRenderEvery(120));
await page.click('#btn-new');
await until('s.state === "playing" && s.mode === "LANDED" && s.body === "earth"', 900_000);

for (const [body, key] of [['moon', 'Digit5'], ['mars', 'Digit6']]) {
  await page.keyboard.press('Tab');
  await page.keyboard.press(key);
  await page.keyboard.press('Tab');
  await until(`s.state === "playing" && s.navTarget === "${body}"`, 60_000);
  await page.evaluate((to) => window.__meridian.autopilot({ kind: 'travel', to }), body);
  await page.waitForFunction(() => window.__meridian.autopilotState().phase === 'landed', null, { timeout: 3 * 60 * 60 * 1000, polling: 1000 });
  await page.evaluate(() => window.__meridian.autopilot(null));
  await until(`s.mode === "LANDED" && s.body === "${body}" && s.bodyShown`, 300_000);
  // Settle on the pad, then export from the pause menu.
  const t0 = (await snap()).simTime;
  await page.waitForFunction((t) => window.__meridian.snapshot().simTime > t + 3, t0, { timeout: 300_000 });
  await page.keyboard.press('Escape');
  await until('s.state === "paused"', 60_000);
  const download = page.waitForEvent('download');
  await page.click('#btn-export');
  const file = join(here, `${body}-landed.json`);
  await (await download).saveAs(file);
  const save = JSON.parse(readFileSync(file, 'utf8'));
  if (save.schema !== 2 || save.system !== 'sol' || save.mode !== 'LANDED' || save.bodyId !== body) throw new Error(`unexpected backup for ${body}: ${JSON.stringify({ schema: save.schema, system: save.system, mode: save.mode, bodyId: save.bodyId })}`);
  console.log(`${body}: wrote ${file} (sim ${save.playTime?.toFixed?.(0)} s, unlocked ${JSON.stringify(save.unlocked)})`);
  await page.click('#btn-resume');
  await until('s.state === "playing"', 60_000);
}
if (errors.length) throw new Error(`page errors: ${errors.join(' | ')}`);
await browser.close();
