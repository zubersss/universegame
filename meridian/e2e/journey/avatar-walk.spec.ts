import { expect, test, type Page } from '@playwright/test';
import { bootToTitle, collectErrors, snap, stubPointerLock } from '../helpers';

// P3/P4: the explorer on foot, driven only through player inputs (real key
// events and the test autopilot's injected keys and mouse look). Exit the
// ship (down the ladder), walk 25+ m with a jump, look up (camera onto the
// ground), toggle the camera, sprint
// back, board (up the ladder), and exit and board twice more; the
// character's animation states, planted-foot slip, camera clearance and
// resources are read through the test API (read-only).

test.use({ viewport: { width: 640, height: 360 } });

const api = (page: Page, fn: string, ...args: unknown[]) =>
  page.evaluate(([f, a]) => (window as any).__meridian[f as string](...(a as unknown[])), [fn, args] as const);
const player = (page: Page): Promise<Record<string, any> | null> => page.evaluate(() => (window as any).__meridian.player.state());

async function until(page: Page, src: string, timeoutMs = 600_000): Promise<Record<string, any>> {
  await page.waitForFunction((s) => new Function('s', `return (${s});`)((window as any).__meridian.snapshot()), src, { timeout: timeoutMs, polling: 300 });
  return snap(page);
}

async function untilPlayer(page: Page, src: string, timeoutMs = 600_000): Promise<Record<string, any>> {
  await page.waitForFunction((s) => new Function('p', `return (${s});`)((window as any).__meridian.player.state()), src, { timeout: timeoutMs, polling: 300 });
  return (await player(page))!;
}

/**
 * Wait for the autopilot to arrive; returns the explorer's state read in the
 * same poll that first saw the arrival (before the body has slowed down).
 */
async function arrive(page: Page, timeoutMs = 600_000): Promise<Record<string, any>> {
  const h = await page.waitForFunction(
    () => {
      const m = (window as any).__meridian;
      return m.autopilotState().phase === 'arrived' ? { ...m.player.state(), snap: m.snapshot() } : null;
    },
    null,
    { timeout: timeoutMs, polling: 100 },
  );
  const at = (await h.jsonValue()) as Record<string, any>;
  await api(page, 'autopilot', null);
  return at;
}

/** Simulation seconds since the test started (for logs). */
async function simTime(page: Page): Promise<number> {
  return (await snap(page)).simTime as number;
}

test('explorer: exit, walk 25 m with a jump, camera toggle, sprint back, board, exit again', async ({ page }) => {
  test.setTimeout(40 * 60 * 1000);
  const errors = collectErrors(page);
  await stubPointerLock(page);
  // system=quiet: Ilex stays the start once Sol becomes the default (LEAD step 10).
  await bootToTitle(page, '?preset=low&system=quiet');
  await page.click('#btn-new');
  let s = await until(page, 's.state === "playing"');
  expect(s.mode).toBe('LANDED');
  expect(await player(page)).toBeNull();
  const scene0 = await page.evaluate(() => (window as any).__meridian.game.render.scene.children.length);

  // Exit with a real key event: the explorer appears in third person.
  await page.keyboard.press('KeyE');
  s = await until(page, 's.mode === "ON_FOOT" && s.player && s.player.grounded', 120_000);
  // The explorer climbs down the ladder first (P4), then stands where the walker is.
  let p = await untilPlayer(page, 'p && p.avatar && p.avatar.entries.climb >= 1', 120_000);
  p = await untilPlayer(page, 'p && p.avatar && p.avatar.attached && p.avatar.state !== "climb" && p.camera.arm > 1', 120_000);
  expect(p.avatar.visible).toBe(true);
  expect(p.camera.mode).toBe('third');
  expect(p.camera.bodyVisible).toBe(true);
  expect(p.avatar.rootToFeet).toBeLessThan(0.15); // on the capsule's feet (interpolation lag + controller skin)
  expect(p.ability).toMatchObject({ state: 'walk', power: null, body: 'ilex' });
  expect(await page.evaluate(() => (window as any).__meridian.game.render.scene.children.length)).toBe(scene0 + 1);
  await page.screenshot({ path: 'evidence/p1-explorer-exit.png', timeout: 180_000 });

  // Walk out 25 m or more (ladder side) with a jump on the way; inputs only.
  await api(page, 'setRenderEvery', 8);
  await page.evaluate(() => (window as any).__meridian.player.resetSlip());
  const start = s.player.system as number[];
  const out = await api(page, 'dirNearShip', -26, -15);
  await api(page, 'autopilot', { kind: 'walk', target: out, arrive: 2, jumpAt: 12 });
  await untilPlayer(page, 'p && p.avatar.state === "walk"', 300_000);
  const atArrival = await arrive(page);
  const end = atArrival.snap.player.system as number[];
  const distance = Math.hypot(end[0] - start[0], end[1] - start[1], end[2] - start[2]);
  console.log(`walked ${distance.toFixed(1)} m`);
  expect(distance).toBeGreaterThanOrEqual(25);
  s = await until(page, 's.player && s.player.grounded && s.player.speed < 0.01', 120_000);
  p = await untilPlayer(page, 'p && p.avatar.state === "idle"', 120_000);
  const walked = p;
  console.log(`walk out done at t=${(await simTime(page)).toFixed(1)}: ${JSON.stringify(walked.avatar)}`);
  expect(s.counters.jumps).toBeGreaterThanOrEqual(1);
  expect(walked.avatar.entries.walk).toBeGreaterThanOrEqual(1);
  expect(walked.avatar.entries.jump + walked.avatar.entries.fall).toBeGreaterThanOrEqual(1);
  expect(walked.avatar.entries.land).toBeGreaterThanOrEqual(1);
  expect(walked.avatar.entries.idle).toBeGreaterThanOrEqual(1);
  // Planted feet never slide (terrain-adapted, measured at the ball of the foot), sampled while walking.
  expect(atArrival.avatar.slipSamplesMoving).toBeGreaterThan(20);
  expect(walked.avatar.maxSlip).toBeLessThan(0.01);
  // Stopping takes at most one settle step per foot (counted from the moment
  // of arrival, while still moving); standing still afterwards: no shuffling.
  let t0 = await simTime(page);
  await until(page, `s.simTime > ${t0 + 1.5}`, 120_000);
  const settled = (await player(page))!.avatar.settleSteps;
  expect(settled - atArrival.avatar.settleSteps).toBeLessThanOrEqual(2);
  t0 = await simTime(page);
  await until(page, `s.simTime > ${t0 + 3}`, 120_000);
  expect((await player(page))!.avatar.settleSteps).toBe(settled);
  // The camera stayed above the ground the whole way (measured after every placement).
  expect(walked.camera.minTerrainClearance).toBeGreaterThanOrEqual(0.4);
  // Looking up swings the arm down behind the explorer onto the ground: the
  // camera stops above the colliders (ray) and the analytic surface.
  await api(page, 'mouse', 0, -600);
  t0 = await simTime(page);
  await until(page, `s.simTime > ${t0 + 1}`, 120_000);
  const lookUp = (await player(page))!;
  console.log(`looking up: ${JSON.stringify(lookUp.camera)}`);
  expect(lookUp.camera.groundGap).toBeGreaterThan(0.15);
  expect(lookUp.camera.altitude).toBeGreaterThan(0.15);
  // The ground did constrain it: the arm was shortened by the colliders or lifted by the analytic clearance.
  expect(lookUp.camera.arm < 4.2 || lookUp.camera.minTerrainClearance < 1.6).toBe(true);
  await api(page, 'mouse', 0, 600);
  await api(page, 'setRenderEvery', 1);
  await page.waitForTimeout(3000);
  await page.screenshot({ path: 'evidence/p1-explorer-out.png', timeout: 180_000 });

  // C toggles first person (body hidden, camera at the eye) and back.
  await page.keyboard.press('KeyC');
  p = await untilPlayer(page, 'p && p.camera.mode === "first"', 120_000);
  await untilPlayer(page, 'p && p.camera.distanceToEye < 0.01 && !p.camera.bodyVisible', 120_000);
  await page.keyboard.press('KeyC');
  p = await untilPlayer(page, 'p && p.camera.mode === "third" && p.camera.bodyVisible && p.camera.arm > 1', 120_000);

  // Sprint back to the ladder: the run cycle.
  await api(page, 'setRenderEvery', 8);
  await page.evaluate(() => (window as any).__meridian.player.resetSlip());
  await api(page, 'autopilot', { kind: 'walk', target: 'ship', arrive: 2.5, sprint: true });
  await untilPlayer(page, 'p && p.avatar.state === "run"', 300_000);
  p = await arrive(page);
  console.log(`sprint back done at t=${(await simTime(page)).toFixed(1)}: ${JSON.stringify(p.avatar)}`);
  expect(p.avatar.entries.run).toBeGreaterThanOrEqual(1);
  expect(p.avatar.slipSamplesMoving).toBeGreaterThan(20);
  expect(p.avatar.maxSlip).toBeLessThan(0.01);

  // Board with a real key event: the explorer climbs the ladder (P4), then leaves the scene.
  await page.keyboard.press('KeyE');
  await untilPlayer(page, 'p && p.avatar.state === "climb"', 60_000);
  s = await until(page, 's.mode === "LANDED"', 60_000);
  expect(await player(page)).toBeNull();
  expect(await page.evaluate(() => (window as any).__meridian.game.render.scene.children.length)).toBe(scene0);

  // Exit and board twice more at the same spot: a fresh explorer each time,
  // and nothing accumulates. Resources are compared between consecutive
  // landed states (drawn at full rate so the renderer's counters are
  // current); the first cycle may still upload lazily created GPU data.
  await api(page, 'setRenderEvery', 1);
  const cycle = async () => {
    await page.keyboard.press('KeyE');
    await until(page, 's.mode === "ON_FOOT" && s.player && s.player.grounded', 120_000);
    await untilPlayer(page, 'p && p.avatar && p.avatar.attached && p.avatar.visible', 120_000);
    expect(await page.evaluate(() => (window as any).__meridian.game.render.scene.children.length)).toBe(scene0 + 1);
    await page.keyboard.press('KeyE');
    await until(page, 's.mode === "LANDED"', 60_000);
    expect(await player(page)).toBeNull();
    expect(await page.evaluate(() => (window as any).__meridian.game.render.scene.children.length)).toBe(scene0);
    const t = await simTime(page);
    await until(page, `s.simTime > ${t + 2}`, 120_000);
    return api(page, 'resources');
  };
  const resA = await cycle();
  const resB = await cycle();
  console.log(`resources landed after exit/board cycles ${JSON.stringify(resA)} then ${JSON.stringify(resB)}`);
  expect(resB.geometries).toBeLessThanOrEqual(resA.geometries + 2);
  expect(resB.textures).toBeLessThanOrEqual(resA.textures);
  expect(resB.bodies).toBe(resA.bodies);
  expect(resB.colliders).toBe(resA.colliders);
  expect(errors).toEqual([]);
});
