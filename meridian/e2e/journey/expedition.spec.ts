import { expect, test, type Page } from '@playwright/test';
import { bootToTitle, collectErrors, snap, stubPointerLock } from '../helpers';

// Phase 7 gate: the complete expedition through normal gameplay — sample,
// relay and scans on all three bodies, travel between them, transmission and
// free play — plus reloads while landed, walking and flying. Interactions use
// real key events (E, F, T, Escape) and menu clicks; movement uses the test
// autopilot, which injects keys and mouse motion only.

test.use({ viewport: { width: 640, height: 360 } });

const api = (page: Page, fn: string, ...args: unknown[]) =>
  page.evaluate(([f, a]) => (window as any).__meridian[f as string](...(a as unknown[])), [fn, args] as const);

async function until(page: Page, src: string, timeoutMs = 600_000): Promise<Record<string, any>> {
  await page.waitForFunction((s) => new Function('s', `return (${s});`)((window as any).__meridian.snapshot()), src, { timeout: timeoutMs, polling: 300 });
  return snap(page);
}

async function apPhase(page: Page, phases: string[], timeoutMs = 600_000): Promise<string> {
  await page.waitForFunction((ps) => ps.includes((window as any).__meridian.autopilotState().phase), phases, { timeout: timeoutMs, polling: 300 });
  return (await api(page, 'autopilotState')).phase;
}

async function walkTo(page: Page, target: unknown, arrive: number): Promise<void> {
  await api(page, 'autopilot', { kind: 'walk', target, arrive, sprint: true });
  await apPhase(page, ['arrived']);
  await api(page, 'autopilot', null);
}

/** Aim at a planet-relative point and hold F until the scan completes. */
async function scan(page: Page, atPlanet: number[]): Promise<Record<string, any>> {
  await api(page, 'autopilot', { kind: 'aim', atPlanet });
  await apPhase(page, ['aimed'], 120_000);
  await page.keyboard.down('KeyF');
  const s = await until(page, 's.scan.done', 120_000);
  await page.keyboard.up('KeyF');
  await api(page, 'autopilot', null);
  return s;
}

async function surveyHere(page: Page, body: string): Promise<void> {
  await page.keyboard.press('KeyE');
  let s = await until(page, 's.mode === "ON_FOOT" && s.player && s.player.grounded', 120_000);
  const targets = (await api(page, 'missionTargets')) as { id: string; kind: string; dir: number[] }[];
  const sample = targets.find((t) => t.kind === 'sample' && !s.expedition.collected.includes(t.id))!;
  const relay = targets.find((t) => t.kind === 'relay')!;
  // Sample: collect once; a second press must not duplicate it.
  await walkTo(page, sample.dir, 1.4);
  s = await snap(page);
  expect(s.interaction?.kind).toBe('sample');
  await page.keyboard.press('KeyE');
  s = await until(page, `s.expedition.collected.includes("${sample.id}")`, 60_000);
  expect(s.expedition.inventory[body]).toBe(1);
  await page.keyboard.press('KeyE');
  await page.waitForTimeout(600);
  s = await snap(page);
  expect(s.expedition.inventory[body]).toBe(1);
  expect(s.expedition.collected.filter((x: string) => x === sample.id).length).toBe(1);
  // Relay: activate once, consuming the sample; repeats change nothing.
  await walkTo(page, relay.dir, 2.2);
  s = await snap(page);
  expect(s.interaction?.kind).toBe('relay');
  await page.keyboard.press('KeyE');
  s = await until(page, `s.expedition.relays.includes("${body}")`, 60_000);
  expect(s.expedition.inventory[body]).toBe(0);
  await page.keyboard.press('KeyE');
  await page.waitForTimeout(600);
  s = await snap(page);
  expect(s.expedition.relays.filter((x: string) => x === body).length).toBe(1);
  expect(s.expedition.inventory[body]).toBe(0);
  // Scan the relay mast and the nearest natural object.
  const relayAt = await page.evaluate(() => {
    const g = (window as any).__meridian.game;
    return g.mission.targets.find((t: any) => t.kind === 'relay').pos.toArray();
  });
  s = await scan(page, relayAt);
  expect(s.expedition.scanned).toContain(relay.id);
  const near = (await api(page, 'nearbyScannables', 250)) as { id: string; species: string; atPlanet: number[]; dir: number[] }[];
  expect(near.length).toBeGreaterThan(0);
  await walkTo(page, near[0].dir, 8);
  s = await scan(page, near[0].atPlanet);
  expect(s.expedition.species).toContain(near[0].species);
  // Back aboard.
  await walkTo(page, 'ship', 2.5);
  await page.keyboard.press('KeyE');
  await until(page, 's.mode === "LANDED"', 60_000);
}

/** Evidence screenshot once nearby props have generated (every frame drawn while capturing). */
async function photo(page: Page, name: string): Promise<void> {
  await until(page, 's.props && s.props.pending === 0', 600_000);
  await api(page, 'setRenderEvery', 1);
  await page.waitForTimeout(5000);
  await page.screenshot({ path: `evidence/${name}.png`, timeout: 180_000 });
  await api(page, 'setRenderEvery', 60);
}

async function saveViaPause(page: Page): Promise<void> {
  await page.keyboard.press('Escape');
  await until(page, 's.state === "paused"', 30_000);
  const before = (await api(page, 'saveState')).latest.savedAt;
  await page.click('#btn-save');
  await page.waitForFunction((b) => {
    const st = (window as any).__meridian.saveState();
    return st.latest.valid && st.latest.savedAt !== b;
  }, before, { timeout: 30_000 });
}

async function reloadAndContinue(page: Page): Promise<Record<string, any>> {
  await page.reload();
  await page.waitForFunction(() => (window as any).__meridianBooted === true, null, { timeout: 180_000 });
  await expect(page.locator('#btn-continue')).toBeVisible();
  await api(page, 'setRenderEvery', 60);
  await page.click('#btn-continue');
  return until(page, 's.state === "playing"', 600_000);
}

test('complete expedition with reloads while landed, walking and flying', async ({ page }) => {
  test.setTimeout(6 * 60 * 60 * 1000);
  const errors = collectErrors(page);
  await stubPointerLock(page);
  await bootToTitle(page, '?preset=low');
  await api(page, 'setRenderEvery', 60);
  await page.click('#btn-new');
  let s = await until(page, 's.state === "playing"');
  expect(s.mode).toBe('LANDED');
  await photo(page, 'phase7-ilex-start');

  // ---- Ilex
  await surveyHere(page, 'ilex');
  s = await snap(page);
  const ilexSpecies = s.expedition.species.length;
  expect(s.navTarget).toBe('vesper'); // course set automatically after the relay
  // Reload while landed.
  await saveViaPause(page);
  s = await reloadAndContinue(page);
  expect(s.mode).toBe('LANDED');
  expect(s.body).toBe('ilex');
  expect(s.expedition.relays).toEqual(['ilex']);
  expect(s.expedition.species.length).toBe(ilexSpecies);

  // ---- Vesper
  await api(page, 'autopilot', { kind: 'travel', to: 'vesper' });
  await apPhase(page, ['landed'], 3 * 60 * 60 * 1000);
  await until(page, 's.mode === "LANDED" && s.body === "vesper"', 120_000);
  await api(page, 'autopilot', null);
  await photo(page, 'phase7-vesper-landed');
  // Reload while walking: collect (autosaves), then reload mid-walk.
  await page.keyboard.press('KeyE');
  s = await until(page, 's.mode === "ON_FOOT" && s.player && s.player.grounded', 120_000);
  const vTargets = (await api(page, 'missionTargets')) as { id: string; kind: string; dir: number[] }[];
  const vSample = vTargets.find((t) => t.kind === 'sample')!;
  await walkTo(page, vSample.dir, 1.4);
  await page.keyboard.press('KeyE');
  await until(page, `s.expedition.collected.includes("${vSample.id}")`, 60_000);
  await page.waitForFunction(() => {
    const st = (window as any).__meridian.saveState();
    return st.latest.valid && st.latest.mode === 'ON_FOOT';
  }, null, { timeout: 60_000 });
  const feetBefore = (await snap(page)).player.system as number[];
  s = await reloadAndContinue(page);
  expect(s.mode).toBe('ON_FOOT');
  expect(s.body).toBe('vesper');
  expect(s.expedition.inventory.vesper).toBe(1);
  const feetAfter = s.player.system as number[];
  expect(Math.hypot(feetAfter[0] - feetBefore[0], feetAfter[1] - feetBefore[1], feetAfter[2] - feetBefore[2])).toBeLessThan(3);
  // Finish Vesper: relay with the carried sample, scans, board.
  await page.keyboard.press('KeyF'); // harmless tap
  const relay = vTargets.find((t) => t.kind === 'relay')!;
  await walkTo(page, relay.dir, 2.2);
  await page.keyboard.press('KeyE');
  s = await until(page, 's.expedition.relays.includes("vesper")', 60_000);
  const near = (await api(page, 'nearbyScannables', 250)) as { species: string; atPlanet: number[]; dir: number[] }[];
  await walkTo(page, near[0].dir, 8);
  s = await scan(page, near[0].atPlanet);
  expect(s.expedition.species).toContain(near[0].species);
  await walkTo(page, 'ship', 2.5);
  await page.keyboard.press('KeyE');
  await until(page, 's.mode === "LANDED"', 60_000);

  // ---- Toward Cairn, with a reload in flight.
  await api(page, 'autopilot', { kind: 'travel', to: 'cairn' });
  await page.waitForFunction(() => {
    const s2 = (window as any).__meridian.snapshot();
    return s2.mode === 'PILOTING' && s2.clearance > 2500;
  }, null, { timeout: 1_800_000, polling: 300 });
  await api(page, 'autopilot', null);
  await saveViaPause(page);
  const flyBefore = await snap(page);
  s = await reloadAndContinue(page);
  expect(s.mode).toBe('PILOTING');
  expect(s.body).toBe('vesper');
  const dp = Math.hypot(...[0, 1, 2].map((i) => s.shipSystem[i] - flyBefore.shipSystem[i]));
  expect(dp).toBeLessThan(200);
  expect(Math.abs(s.speed - flyBefore.speed)).toBeLessThan(60);
  await api(page, 'autopilot', { kind: 'travel', to: 'cairn' });
  await apPhase(page, ['landed'], 3 * 60 * 60 * 1000);
  await until(page, 's.mode === "LANDED" && s.body === "cairn"', 120_000);
  await api(page, 'autopilot', null);
  await photo(page, 'phase7-cairn-landed');
  await surveyHere(page, 'cairn');

  // ---- Transmit from the ship, then free play continues.
  s = await snap(page);
  expect(s.expedition.relays.sort()).toEqual(['cairn', 'ilex', 'vesper']);
  await page.keyboard.press('KeyT');
  s = await until(page, 's.expedition.transmitted === true', 30_000);
  expect(s.counters.transmissions).toBe(1);
  await page.keyboard.press('KeyT');
  await page.waitForTimeout(500);
  expect((await snap(page)).counters.transmissions).toBe(1);
  await api(page, 'setRenderEvery', 1);
  await page.waitForTimeout(3000);
  await page.screenshot({ path: 'evidence/phase7-transmitted.png', timeout: 180_000 });
  await api(page, 'setRenderEvery', 60);
  await page.keyboard.press('Space');
  s = await until(page, 's.mode === "PILOTING" && s.clearance > 20', 120_000);
  expect(s.expedition.transmitted).toBe(true);
  expect(s.counters.recoveries).toBe(0);
  expect(errors).toEqual([]);
});
