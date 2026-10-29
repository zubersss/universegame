import { expect, test, type Page } from '@playwright/test';
import { bootToTitle, collectErrors, snap, stubPointerLock } from '../helpers';

// Per-merge quick journey (GAUGE, studio round): one short pass through the
// core loop on the starting body, fast enough to run after every merge to
// studio/integration (target ≤ 15 min in software rendering). Real Play click
// → take off → short flight → assisted landing on a surveyed flat site →
// exit → walk → scan the nearest scannable → board → take off, with zero
// console errors. Movement uses the test autopilot (injected keys and mouse
// motion only); E, F and Space are real key events. Rendering is throttled
// and pointer lock stubbed (lesson A8.5).

test.use({ viewport: { width: 640, height: 360 } });

const api = (page: Page, fn: string, ...args: unknown[]) =>
  page.evaluate(([f, a]) => (window as any).__meridian[f as string](...(a as unknown[])), [fn, args] as const);

async function until(page: Page, src: string, timeoutMs = 300_000): Promise<Record<string, any>> {
  await page.waitForFunction((s) => new Function('s', `return (${s});`)((window as any).__meridian.snapshot()), src, { timeout: timeoutMs, polling: 300 });
  return snap(page);
}

async function apPhase(page: Page, phases: string[], timeoutMs = 300_000): Promise<string> {
  await page.waitForFunction((ps) => ps.includes((window as any).__meridian.autopilotState().phase), phases, { timeout: timeoutMs, polling: 300 });
  return (await api(page, 'autopilotState')).phase;
}

async function walkTo(page: Page, target: unknown, arrive: number): Promise<void> {
  await api(page, 'autopilot', { kind: 'walk', target, arrive });
  await apPhase(page, ['arrived']);
  await api(page, 'autopilot', null);
}

test('quick journey: take off, land, walk, scan, board, take off', async ({ page }) => {
  test.setTimeout(20 * 60 * 1000);
  const t0 = Date.now();
  const lap = (what: string) => console.log(`${((Date.now() - t0) / 1000).toFixed(0).padStart(4)} s  ${what}`);
  const errors = collectErrors(page);
  await stubPointerLock(page);
  await bootToTitle(page, '?preset=low');
  await api(page, 'setRenderEvery', 60);
  await page.click('#btn-new');
  let s = await until(page, 's.state === "playing"');
  expect(s.mode).toBe('LANDED');
  const body = s.body as string;
  lap(`playing, landed on ${body}`);

  // Take off (real key) and fly a short stretch.
  await page.keyboard.press('Space');
  s = await until(page, 's.mode === "PILOTING" && s.clearance > 15', 120_000);
  await api(page, 'autopilot', { kind: 'fly', dir: null, clearance: 90, throttle: 0.4 });
  const tFly = s.simTime as number;
  s = await until(page, `s.simTime > ${tFly + 8} && s.clearance > 40`, 300_000);
  expect(s.speed).toBeGreaterThan(5);
  lap(`flying: clearance ${s.clearance.toFixed(0)} m, speed ${s.speed.toFixed(0)} m/s`);

  // Assisted landing on a surveyed flat site (next candidate if the assist refuses one).
  const sv = await api(page, 'surveySites', 3, 250, 700);
  expect(sv.flat.length).toBeGreaterThan(0);
  let landed = false;
  for (const dir of sv.flat) {
    await api(page, 'autopilot', { kind: 'land', dir, approachClearance: 70 });
    if ((await apPhase(page, ['landed', 'rejected'], 600_000)) === 'landed') {
      landed = true;
      break;
    }
    await api(page, 'autopilot', null);
    await page.keyboard.press('KeyL');
    lap('site refused by the landing assist, trying the next one');
  }
  expect(landed).toBe(true);
  s = await until(page, 's.mode === "LANDED"', 60_000);
  expect(s.probe.reason).toBeNull();
  expect(s.probe.slope).toBeLessThanOrEqual(12);
  expect(s.body).toBe(body);
  await api(page, 'autopilot', null);
  lap(`landed, slope ${s.probe.slope.toFixed(1)}°`);

  // Exit (real key) and walk out on the ladder side.
  await page.keyboard.press('KeyE');
  s = await until(page, 's.mode === "ON_FOOT" && s.player && s.player.grounded', 60_000);
  await walkTo(page, await api(page, 'dirNearShip', -16, 6), 2);
  lap('walked out');

  // Scan the nearest scannable prop: walk within range, aim, hold F (real key).
  const near = (await api(page, 'nearbyScannables', 300)) as { id: string; species: string; atPlanet: number[]; dir: number[] }[];
  expect(near.length).toBeGreaterThan(0);
  await walkTo(page, near[0].dir, 8);
  await api(page, 'autopilot', { kind: 'aim', atPlanet: near[0].atPlanet });
  await apPhase(page, ['aimed'], 120_000);
  await page.keyboard.down('KeyF');
  s = await until(page, 's.scan.done', 120_000);
  await page.keyboard.up('KeyF');
  await api(page, 'autopilot', null);
  expect(s.expedition.species).toContain(near[0].species);
  lap(`scanned ${near[0].species}`);

  // Board (real key) and take off again.
  await walkTo(page, 'ship', 2.5);
  await page.keyboard.press('KeyE');
  await until(page, 's.mode === "LANDED"', 60_000);
  await page.keyboard.press('Space');
  s = await until(page, 's.mode === "PILOTING" && s.clearance > 15', 120_000);
  lap('boarded and took off');

  expect(s.counters.landings).toBeGreaterThanOrEqual(1);
  expect(s.counters.exits).toBeGreaterThanOrEqual(1);
  expect(s.counters.boardings).toBeGreaterThanOrEqual(1);
  expect(s.counters.takeoffs).toBeGreaterThanOrEqual(2);
  expect(s.counters.recoveries).toBe(0);
  expect(errors).toEqual([]);
});
