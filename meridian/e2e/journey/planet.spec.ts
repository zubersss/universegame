import { expect, test, type Page } from '@playwright/test';
import { bootToTitle, collectErrors, snap } from '../helpers';

// Phase 3 gate: continuous planet. Fly low from the landing site across a
// cube-face boundary, climb above the atmosphere, then return to low altitude.
// Throughout: no holes/overlap (every quadtree leaf rendered), never below the
// terrain, multiple origin rebases, bounded colliders, no console errors.

test.use({ viewport: { width: 640, height: 360 } });

interface Watch {
  minClearance: number;
  maxAltitude: number;
  faces: Set<number>;
  coverageFailures: number;
  maxColliders: number;
  samples: number;
}

async function monitor(page: Page, w: Watch, until: string, timeoutMs: number, label: string): Promise<Record<string, any>> {
  const deadline = Date.now() + timeoutMs;
  for (;;) {
    const r = await page.evaluate((src) => {
      const api = (window as any).__meridian;
      const s = api.snapshot();
      return {
        s,
        cov: api.terrainCoverageOk(),
        face: api.faceUnderShip(),
        ap: api.autopilotState(),
        done: new Function('s', `return (${src});`)(s),
      };
    }, until);
    w.samples++;
    if (r.s.terrain.coarseReady && !r.cov) w.coverageFailures++;
    w.minClearance = Math.min(w.minClearance, r.s.clearance);
    w.maxAltitude = Math.max(w.maxAltitude, r.s.altitude);
    w.maxColliders = Math.max(w.maxColliders, r.s.terrain.colliders);
    w.faces.add(r.face);
    if (r.done) {
      console.log(`${label}: t=${r.s.simTime.toFixed(1)} alt=${r.s.altitude.toFixed(0)} clr=${r.s.clearance.toFixed(0)} spd=${r.s.speed.toFixed(0)} face=${r.face} rebases=${r.s.rebaseCount} dist=${(r.ap.distance / 1000).toFixed(1)}km leaves=${r.s.terrain.leaves} maxL=${r.s.terrain.maxLevel} colliders=${r.s.terrain.colliders}`);
      return r.s;
    }
    if (Date.now() > deadline) throw new Error(`${label}: timed out (t=${r.s.simTime}, clr=${r.s.clearance}, dist=${r.ap.distance})`);
    await page.waitForTimeout(1500);
  }
}

test('continuous planet: face crossing, atmosphere exit and return', async ({ page }) => {
  test.setTimeout(75 * 60 * 1000);
  const errors = collectErrors(page);
  await bootToTitle(page, '?preset=low&system=quiet'); // pinned: this gate is about the Quiet System planet
  // Software rendering: draw every 16th frame so simulation runs near real time.
  await page.evaluate(() => (window as any).__meridian.setRenderEvery(16));
  await page.click('#btn-new');
  await page.waitForFunction(() => (window as any).__meridian.snapshot().state === 'playing', null, { timeout: 600_000 });
  // The expedition starts landed: take off first.
  await page.keyboard.press('Space');
  await page.waitForFunction(() => (window as any).__meridian.snapshot().mode === 'PILOTING', null, { timeout: 120_000 });
  const w: Watch = { minClearance: Infinity, maxAltitude: 0, faces: new Set(), coverageFailures: 0, maxColliders: 0, samples: 0 };
  const startFace = await page.evaluate(() => (window as any).__meridian.faceUnderShip());
  const target = await page.evaluate(() => (window as any).__meridian.faceEdgeTarget(6000));

  // 1) Low, fast flight toward and across the face boundary.
  await page.evaluate((dir) => (window as any).__meridian.autopilot({ kind: 'fly', dir, clearance: 1300, throttle: 1, boost: true }), target);
  await monitor(page, w, 's.clearance > 1000', 1_200_000, 'climb-out');
  const crossed = await monitor(
    page, w,
    `(window.__meridian.faceUnderShip() !== ${startFace})`,
    3_000_000, 'face-crossed',
  );
  await monitor(page, w, `s.simTime > ${crossed.simTime + 8}`, 900_000, 'past-boundary');

  // 2) Climb above the atmosphere (8 km) into space.
  await page.evaluate((dir) => (window as any).__meridian.autopilot({ kind: 'fly', dir, clearance: 14000, throttle: 1, boost: true, pitchDeg: 35 }), target);
  const high = await monitor(page, w, 's.altitude > 10000', 3_000_000, 'above-atmosphere');
  expect(high.speedCap).toBeGreaterThan(400);

  // 3) Return to low altitude.
  await page.evaluate((dir) => (window as any).__meridian.autopilot({ kind: 'fly', dir, clearance: 250, throttle: 0.6, pitchDeg: -25 }), target);
  await monitor(page, w, 's.clearance < 600', 3_000_000, 'descended');
  await page.evaluate(() => (window as any).__meridian.autopilot({ kind: 'fly', dir: null, clearance: 250, throttle: 0.4 }));
  const end = await monitor(page, w, 's.clearance < 400 && Math.abs(s.verticalSpeed) < 25', 1_500_000, 'low-again');
  await page.evaluate(() => (window as any).__meridian.setRenderEvery(1));
  await page.waitForTimeout(3000);
  await page.screenshot({ path: 'evidence/phase3-return-low.png' });
  await page.evaluate(() => (window as any).__meridian.autopilot(null));

  console.log(`samples=${w.samples} minClearance=${w.minClearance.toFixed(1)} maxAltitude=${w.maxAltitude.toFixed(0)} faces=${[...w.faces].join(',')} coverageFailures=${w.coverageFailures} maxColliders=${w.maxColliders}`);
  console.log(`chunks: ${JSON.stringify(end.chunks)} physics: ${JSON.stringify(end.physics)} draw: ${JSON.stringify(end.draw)}`);
  expect(w.faces.size).toBeGreaterThanOrEqual(2);
  expect(w.maxAltitude).toBeGreaterThan(10000);
  expect(w.minClearance).toBeGreaterThan(2);
  expect(w.coverageFailures).toBe(0);
  expect(w.maxColliders).toBeLessThanOrEqual(48);
  expect(end.rebaseCount).toBeGreaterThanOrEqual(3);
  expect(end.chunks.errors).toBe(0);
  const s = await snap(page);
  expect(s.terrain.coarseReady).toBe(true);
  expect(errors).toEqual([]);
});
