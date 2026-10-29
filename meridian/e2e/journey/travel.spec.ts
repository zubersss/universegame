import { expect, test, type Page } from '@playwright/test';
import { bootToTitle, collectErrors, snap, stubPointerLock } from '../helpers';

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
async function fingerprint(page: Page, body: string): Promise<any> {
  await page.waitForFunction((b) => {
    const f = (window as any).__meridian.fingerprint(b);
    return f && f.pendingCells === 0 && f.props.length > 0 && !f.contact.includes('miss') && f.contact.filter((c: string | null) => c !== null).length >= 2;
  }, body, { timeout: 600_000, polling: 1000 });
  const f = await api(page, 'fingerprint', body);
  delete f.pendingCells;
  return f;
}

async function apPhase(page: Page, phases: string[], timeoutMs: number): Promise<string> {
  await page.waitForFunction((ps) => ps.includes((window as any).__meridian.autopilotState().phase), phases, { timeout: timeoutMs, polling: 500 });
  return (await api(page, 'autopilotState')).phase;
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
  // Route over every body in BODY_IDS, back to the start: Ilex → Vesper → Cairn → Ilex
  // with the core bodies; new bodies extend each round automatically (budget the
  // time). TRAVEL_BODIES=ilex,vesper,cairn restricts the gate to the listed bodies.
  const only = process.env.TRAVEL_BODIES?.split(',').map((x) => x.trim()).filter(Boolean);
  const all = (await api(page, 'bodies')) as { id: string; airless: boolean }[];
  const bodies = only ? all.filter((b) => only.includes(b.id)) : all;
  if (only) expect(bodies.map((b) => b.id).sort()).toEqual([...only].sort());
  const start = s.body as string;
  const route = [...bodies.map((b) => b.id).filter((id) => id !== start), start];
  const airless = new Set(bodies.filter((b) => b.airless).map((b) => b.id));
  const legs = route.length;
  const prints: Record<string, any> = {};
  const resources: Record<string, any>[] = [];
  const log: string[] = [];
  prints[start] = await fingerprint(page, start);
  expect(prints[start].props.length).toBeGreaterThan(0);

  for (let round = 0; round < 3; round++) {
    for (const to of route) {
      const t0 = (await snap(page)).simTime as number;
      await api(page, 'autopilot', { kind: 'travel', to, brakeAt: round === 0 && to === route[0] ? 0.35 : undefined });
      await apPhase(page, ['landed'], 3 * 60 * 60 * 1000);
      s = await until(page, `s.mode === "LANDED" && s.body === "${to}" && s.bodyShown`, 120_000);
      await api(page, 'autopilot', null);
      expect(s.probe.slope).toBeLessThanOrEqual(12);
      // Same geography and placement as the first visit.
      const fp = await fingerprint(page, to);
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
      if (round === 0 && airless.has(to)) {
        // Airless: no sky scattering, no clouds, stars visible.
        const sky = await page.evaluate(() => {
          const g = (window as any).__meridian.game;
          return { atmo: g.ref.atmosphere !== null, sky: g.lighting.skyColor.toArray(), clouds: g.clouds.group.children.length };
        });
        expect(sky.atmo).toBe(false);
        expect(sky.clouds).toBe(0);
        expect(Math.max(...sky.sky)).toBeLessThan(0.05);
      }
      if (round === 0 && to !== start) {
        await api(page, 'setRenderEvery', 1);
        await page.waitForTimeout(3000);
        await page.screenshot({ path: `evidence/phase6-${to}-landed.png`, timeout: 180_000 });
        await api(page, 'setRenderEvery', 120);
      }
    }
  }
  s = await snap(page);
  console.log(log.join('\n'));
  const c = s.counters;
  expect(c.cruiseExitSafety).toBe(0);
  expect(s.cruise.safetyStops).toBe(0);
  expect(c.cruiseExitApproach).toBeGreaterThanOrEqual(3 * legs);
  expect(c.cruiseExitBrake).toBeGreaterThanOrEqual(1);
  expect(c.cruiseExitToggle).toBeGreaterThanOrEqual(1);
  expect(c.landings).toBeGreaterThanOrEqual(3 * legs);
  expect(c.recoveries).toBe(0);
  // Bounded resources: the last round's counts stay close to the first round's.
  for (const key of ['geometries', 'textures', 'bodies', 'colliders', 'cacheCount']) {
    const first = resources.slice(0, legs).map((r) => Number(r[key]));
    const last = resources.slice(2 * legs, 3 * legs).map((r) => Number(r[key]));
    for (let i = 0; i < legs; i++) expect(last[i]).toBeLessThanOrEqual(Math.max(first[i] * 1.25, first[i] + 20));
  }
  expect(errors).toEqual([]);
});
