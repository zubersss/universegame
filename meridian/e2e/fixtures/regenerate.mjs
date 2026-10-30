// Regenerates the landed-save fixtures the power journeys import
// (e2e/journey/powers-*.spec.ts): moon-landed.json and mars-landed.json.
//
// Each is a real backup exported from a run, never hand-edited: a new Sol
// expedition starts landed on Earth; the navigation panel (Tab, then the body's
// key) sets the course; the test autopilot flies there through player inputs
// only and lands; the pause menu's Export writes the backup. Every body is a
// separate expedition flown straight from Earth.
//
// Run against a test build (npm run build:test, then
// npx vite preview --outDir dist-test --port 4174):
//   node e2e/fixtures/regenerate.mjs [baseURL] [bodies, default moon,mars]
// Regenerate whenever the save schema, the Sol start or the landing sites change
// (the journeys fail with "regenerate fixture" when an import no longer works).

import { chromium } from 'playwright';
import { readFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const base = process.argv[2] ?? 'http://localhost:4174/';
const bodies = (process.argv[3] ?? 'moon,mars').split(',');
const KEYS = { moon: 'Digit5', mars: 'Digit6' };
const here = dirname(fileURLToPath(import.meta.url));

const browser = await chromium.launch({ args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] });
for (const body of bodies) {
  if (!KEYS[body]) throw new Error(`no fixture for ${body}`);
  // A fresh profile: no earlier save, a new expedition on Earth.
  const context = await browser.newContext({ viewport: { width: 960, height: 540 }, acceptDownloads: true });
  const page = await context.newPage();
  const errors = [];
  page.on('pageerror', (e) => errors.push(e.message));
  await page.addInitScript(() => {
    Element.prototype.requestPointerLock = function () {
      return Promise.resolve();
    };
  });
  const until = (cond, timeout) => page.waitForFunction(`(() => { const s = window.__meridian.snapshot(); return ${cond}; })()`, null, { timeout, polling: 500 });

  await page.goto(new URL('?preset=low&system=sol', base).toString());
  await page.waitForFunction(() => window.__meridianBooted === true, null, { timeout: 300_000 });
  await page.evaluate(() => window.__meridian.setRenderEvery(120));
  await page.click('#btn-new');
  await until('s.state === "playing" && s.mode === "LANDED" && s.body === "earth"', 900_000);
  await page.keyboard.press('Tab');
  await page.keyboard.press(KEYS[body]);
  await page.keyboard.press('Tab');
  await until(`s.state === "playing" && s.navTarget === "${body}"`, 60_000);
  await page.evaluate((to) => window.__meridian.autopilot({ kind: 'travel', to }), body);
  // Progress every 30 s (wall time) until the autopilot has landed. A cruise
  // leg can end just inside a body's safety envelope (the route passes the
  // Sun on the way to Mars); the autopilot then keeps asking for cruise and is
  // refused. Restarting the travel goal climbs clear of every envelope first
  // and plans the route again from there.
  let refusedAtStart = 0;
  let restarts = 0;
  for (let polls = 0; ; polls++) {
    const st = await page.evaluate(() => ({
      ap: window.__meridian.autopilotState(),
      s: window.__meridian.snapshot(),
      notice: (document.querySelector('#notices')?.textContent ?? '').replace(/\s+/g, ' ').trim().slice(0, 160),
    }));
    if (st.ap.phase === 'landed') break;
    if (polls > 3 * 720) throw new Error(`no landing on ${body} after 3 h: ${JSON.stringify(st.ap)}`);
    if (st.s.counters.cruiseRefused - refusedAtStart >= 3 && (st.ap.phase === 'align' || st.ap.phase === 'engage')) {
      if (++restarts > 10) throw new Error(`cruise refused after ${restarts - 1} restarts: ${st.notice}`);
      console.log(`${body}: restart ${restarts} at sim ${st.s.simTime.toFixed(0)} s, cruise refused ${st.s.counters.cruiseRefused} times (${st.notice.slice(-80)})`);
      refusedAtStart = st.s.counters.cruiseRefused;
      await page.evaluate((to) => {
        window.__meridian.autopilot(null);
        window.__meridian.autopilot({ kind: 'travel', to });
      }, body);
    }
    if (polls % 6 === 0) {
      const c = st.s.counters;
      console.log(`${body}: sim ${st.s.simTime.toFixed(0)} s, ${st.s.mode} at ${st.s.body}, autopilot ${st.ap.phase} (wp ${st.ap.wp}/${st.ap.route.length}, ${(st.ap.distance / 1000).toFixed(1)} km), cruise engages ${c.cruiseEngages} refused ${c.cruiseRefused}; notices: ${st.notice || '-'}`);
    }
    await page.waitForTimeout(5000);
  }
  await page.evaluate(() => window.__meridian.autopilot(null));
  await until(`s.mode === "LANDED" && s.body === "${body}" && s.bodyShown`, 300_000);
  // Settle on the pad, then export from the pause menu.
  const t0 = await page.evaluate(() => window.__meridian.snapshot().simTime);
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
  if (errors.length) throw new Error(`page errors: ${errors.join(' | ')}`);
  await context.close();
}
await browser.close();
