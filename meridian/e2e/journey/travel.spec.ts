import { expect, test, type Page } from '@playwright/test';
import { bootToTitle, collectErrors, snap, stubPointerLock } from '../helpers';
import { CRUISE_MIN_MAX_SPEED, cruiseMaxSpeed } from '../../src/world/scale';

// Phase 6 gate: continuous travel Ilex → Vesper → Cairn → Ilex at production
// distances, landing on each body, three times. Flight, cruise and landing are
// driven only through player inputs (the test autopilot injects keys and mouse
// motion). Checks: brake/cancel and automatic cruise exit, no safety-sphere
// crossings, Cairn airless, identical geography/placement on return visits, and
// bounded resource counts across rounds.

test.use({ viewport: { width: 640, height: 360 } });

const api = (page: Page, fn: string, ...args: unknown[]) =>
  page.evaluate(([f, a]) => (window as any).__meridian[f as string](...(a as unknown[])), [fn, args] as const);

async function until(page: Page, src: string, timeoutMs: number): Promise<Record<string, any>> {
  await page.waitForFunction((s) => new Function('s', `return (${s});`)((window as any).__meridian.snapshot()), src, { timeout: timeoutMs, polling: 500 });
  return snap(page);
}

/** Fingerprint once prop cells near the site have finished generating. */
async function fingerprint(page: Page): Promise<any> {
  await page.waitForFunction(() => {
    const f = (window as any).__meridian.fingerprint();
    return f && f.pendingCells === 0 && f.props.length > 0 && !f.contact.includes('miss') && f.contact.filter((c: string | null) => c !== null).length >= 2;
  }, null, { timeout: 600_000, polling: 1000 });
  const f = await api(page, 'fingerprint');
  delete f.pendingCells;
  return f;
}

async function apPhase(page: Page, phases: string[], timeoutMs: number): Promise<string> {
  await page.waitForFunction((ps) => ps.includes((window as any).__meridian.autopilotState().phase), phases, { timeout: timeoutMs, polling: 500 });
  return (await api(page, 'autopilotState')).phase;
}

/** Angle (degrees) between two unit vectors. */
function angleDeg(a: number[], b: number[]): number {
  const d = a[0] * b[0] + a[1] * b[1] + a[2] * b[2];
  return (Math.acos(Math.max(-1, Math.min(1, d))) * 180) / Math.PI;
}

test('three continuous Ilex → Vesper → Cairn → Ilex routes with landings', async ({ page }) => {
  test.setTimeout(8 * 60 * 60 * 1000);
  const errors = collectErrors(page);
  await stubPointerLock(page);
  await bootToTitle(page, '?preset=low');
  await api(page, 'setRenderEvery', 120);
  await page.click('#btn-new');
  let s = await until(page, 's.state === "playing"', 600_000);
  expect(s.mode).toBe('LANDED');
  const prints: Record<string, any> = {};
  const resources: Record<string, any>[] = [];
  const log: string[] = [];
  prints.ilex = await fingerprint(page);
  expect(prints.ilex.props.length).toBeGreaterThan(0);

  for (let round = 0; round < 3; round++) {
    for (const to of ['vesper', 'cairn', 'ilex']) {
      const t0 = (await snap(page)).simTime as number;
      await api(page, 'autopilot', { kind: 'travel', to, brakeAt: round === 0 && to === 'vesper' ? 0.35 : undefined });
      await apPhase(page, ['landed'], 3 * 60 * 60 * 1000);
      s = await until(page, `s.mode === "LANDED" && s.body === "${to}" && s.bodyShown`, 120_000);
      await api(page, 'autopilot', null);
      expect(s.probe.slope).toBeLessThanOrEqual(12);
      // Same geography and placement as the first visit.
      const fp = await fingerprint(page);
      if (!prints[to]) prints[to] = fp;
      else {
        // Generator heights and every prop's ID and position must match exactly;
        // collision-mesh heights must match wherever both visits had colliders.
        expect(fp.heights).toEqual(prints[to].heights);
        expect(fp.props).toEqual(prints[to].props);
        let compared = 0;
        fp.contact.forEach((c: string | null, i: number) => {
          const p0 = prints[to].contact[i];
          if (c !== null && p0 !== null) {
            expect(c).toBe(p0);
            compared++;
          }
        });
        expect(compared).toBeGreaterThanOrEqual(1);
      }
      const r = await api(page, 'resources');
      resources.push({ round, to, ...r });
      const c = s.counters;
      const line = `round ${round + 1} → ${to}: leg ${(s.simTime - t0).toFixed(0)} s sim · cruise engages ${c.cruiseEngages}, exits approach ${c.cruiseExitApproach} / brake ${c.cruiseExitBrake} / toggle ${c.cruiseExitToggle} / safety ${c.cruiseExitSafety} · activations ${c.activations} releases ${c.releases} (not coarse ${c.releasesNotCoarse}) · geometries ${r.geometries} textures ${r.textures} bodies ${r.bodies} colliders ${r.colliders} cache ${Number(r.cacheMB).toFixed(1)} MB heap ${r.heapMB === null ? 'n/a' : Number(r.heapMB).toFixed(0) + ' MB'}`;
      console.log(line);
      log.push(line);
      if (round === 0 && to === 'cairn') {
        // Airless: no sky scattering, no clouds, stars visible.
        const sky = await page.evaluate(() => {
          const g = (window as any).__meridian.game;
          return { atmo: g.ref.atmosphere !== null, sky: g.lighting.skyColor.toArray(), clouds: g.clouds.group.children.length };
        });
        expect(sky.atmo).toBe(false);
        expect(sky.clouds).toBe(0);
        expect(Math.max(...sky.sky)).toBeLessThan(0.05);
        await api(page, 'setRenderEvery', 1);
        await page.waitForTimeout(3000);
        await page.screenshot({ path: 'evidence/phase6-cairn-landed.png', timeout: 180_000 });
        await api(page, 'setRenderEvery', 120);
      }
      if (round === 0 && to === 'vesper') {
        await api(page, 'setRenderEvery', 1);
        await page.waitForTimeout(3000);
        await page.screenshot({ path: 'evidence/phase6-vesper-landed.png', timeout: 180_000 });
        await api(page, 'setRenderEvery', 120);
      }
    }
  }
  s = await snap(page);
  console.log(log.join('\n'));
  const c = s.counters;
  expect(c.cruiseExitSafety).toBe(0);
  expect(s.cruise.safetyStops).toBe(0);
  expect(c.cruiseExitApproach).toBeGreaterThanOrEqual(9);
  expect(c.cruiseExitBrake).toBeGreaterThanOrEqual(1);
  expect(c.cruiseExitToggle).toBeGreaterThanOrEqual(1);
  expect(c.landings).toBeGreaterThanOrEqual(9);
  expect(c.recoveries).toBe(0);
  // Bounded resources: the last round's counts stay close to the first round's.
  for (const key of ['geometries', 'textures', 'bodies', 'colliders', 'cacheCount']) {
    const first = resources.slice(0, 3).map((r) => Number(r[key]));
    const last = resources.slice(6, 9).map((r) => Number(r[key]));
    for (let i = 0; i < 3; i++) expect(last[i]).toBeLessThanOrEqual(Math.max(first[i] * 1.25, first[i] + 20));
  }
  expect(errors).toEqual([]);
});

// L7b/L6b: Sol behind ?system=sol (about 10-15 min on software rendering).
// New Expedition starts landed on Earth; Tab + 5 sets course for the Moon
// through the navigation panel; the autopilot flies there through player
// inputs only and lands. Checks: every cruise leg is capped by the route it
// planned (the bypass around Earth first) and never passes that cap, the handoff
// releases Earth before it activates the Moon (and nothing else ever
// activates), the landing is level, the light follows each body's sun
// direction, and the console stays clean.
test('Sol: Earth -> Moon hop', async ({ page }) => {
  test.setTimeout(60 * 60 * 1000);
  const errors = collectErrors(page);
  await stubPointerLock(page);
  await bootToTitle(page, '?preset=low&system=sol');
  await api(page, 'setRenderEvery', 120);
  await page.click('#btn-new');
  let s = await until(page, 's.state === "playing"', 600_000);
  expect(s.system).toBe('sol');
  expect(s.mode).toBe('LANDED');
  expect(s.body).toBe('earth');
  expect(s.bodyShown).toBe(true);
  // The opening pose is the first safe landing (Recover has a target from the start).
  expect(await page.evaluate(() => (window as any).__meridian.game.lastSafeLanding?.bodyId ?? null)).toBe('earth');
  // On a body the light comes from that body's sun direction (snapped at placement).
  expect(angleDeg(s.light.dir, s.light.bodySunDir)).toBeLessThanOrEqual(0.5);

  // Navigation: the ten bodies in play with keys 1-0; 5 is the Moon.
  await page.keyboard.press('Tab');
  await expect(page.locator('#panel-nav')).toBeVisible();
  const rows = page.locator('#nav-list .navrow');
  await expect(rows).toHaveCount(10);
  await expect(rows.nth(0).locator('.meta')).toHaveText(/^Star · /);
  await expect(rows.nth(3).locator('.name')).toHaveText(/^4\s+Earth · here/);
  await expect(rows.nth(4).locator('.name')).toHaveText(/^5\s+Moon/);
  await expect(rows.nth(4).locator('.meta')).toHaveText(/^Moon · Landing site/);
  await expect(rows.nth(9).locator('.name')).toHaveText(/^0\s+Neptune/);
  await page.keyboard.press('Digit5');
  await expect(page.locator('#nav-list .navrow.selected .name')).toHaveText(/Moon/);
  await page.keyboard.press('Tab');
  await expect(page.locator('#panel-nav')).toBeHidden();
  s = await until(page, 's.state === "playing"', 60_000);
  expect(s.navTarget).toBe('moon');

  await api(page, 'autopilot', { kind: 'travel', to: 'moon' });
  await apPhase(page, ['landed'], 50 * 60 * 1000);
  s = await until(page, 's.mode === "LANDED" && s.body === "moon" && s.bodyShown', 120_000);
  await api(page, 'autopilot', null);
  console.log(`legs: ${JSON.stringify(s.cruiseLog)}\nhandoffs: ${JSON.stringify(s.handoffLog)}`);

  // Cruise: the opening site is on Earth's far side from the Moon, so the route
  // bypasses Earth (a detour waypoint, then the gate above the Moon's landing
  // site, then the radial leg in) and the first leg is capped for that longer
  // hop: about 30.9 km/s above the site, 29-33.5 km/s wherever the climb can end
  // (within 15° of the site, 10-60 km outside Earth's envelope; checked in
  // tests/sol-boot.test.ts), not the 21 km/s of a start facing the Moon. Every
  // leg is capped by the hop it planned, enters from flight below the 15 km/s
  // floor, never passes its cap and lasts at most 60 s; no safety stop.
  const legs = s.cruiseLog as { start: number; end: number; target: string | null; hop: number; cap: number; entry: number; peak: number; exit: string }[];
  expect(legs.length).toBeGreaterThanOrEqual(3);
  expect(legs[0].cap).toBeGreaterThan(29000);
  expect(legs[0].cap).toBeLessThan(33500);
  for (const l of legs) {
    expect(l.target).toBe('moon');
    expect(l.cap).toBe(cruiseMaxSpeed(l.hop));
    expect(l.entry).toBeLessThan(CRUISE_MIN_MAX_SPEED);
    expect(l.peak).toBeLessThanOrEqual(l.cap);
    expect(l.end - l.start).toBeLessThanOrEqual(60);
  }
  expect(legs.some((l) => l.exit === 'approach')).toBe(true);
  expect(s.counters.cruiseExitSafety).toBe(0);
  expect(s.cruise.safetyStops).toBe(0);

  // Handoff: Earth is released before the Moon activates; only those two ever activate.
  const events = (s.handoffLog as { event: string; body: string }[]).map((e) => `${e.event} ${e.body}`);
  const released = events.indexOf('release earth');
  expect(released).toBeGreaterThanOrEqual(0);
  expect(events.indexOf('activate moon')).toBeGreaterThan(released);
  expect(events.filter((e) => e.startsWith('activate'))).toEqual(['activate earth', 'activate moon']);

  // Landed level, in the Moon's light, with the arrival recorded.
  expect(s.probe.slope).toBeLessThanOrEqual(12);
  expect(angleDeg(s.light.dir, s.light.bodySunDir)).toBeLessThanOrEqual(0.5);
  expect(s.discoveries).toEqual(['earth', 'moon']);
  expect(await page.evaluate(() => (window as any).__meridian.game.lastSafeLanding?.bodyId ?? null)).toBe('moon');

  await api(page, 'setRenderEvery', 1);
  await page.waitForTimeout(3000);
  await page.screenshot({ path: 'evidence/l7b-moon-landed.png', timeout: 180_000 });
  expect(errors).toEqual([]);
});
