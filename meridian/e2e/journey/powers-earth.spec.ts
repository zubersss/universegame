import { expect, test } from '@playwright/test';
import { bootToTitle, collectErrors, snap, stubPointerLock } from '../helpers';
import { api, exitShip, holdFor, holdUntil, power, transitions, until, untilPower } from '../fixtures/powers';
import { ABILITIES } from '../../src/abilities/catalog';
import type { FlightParams } from '../../src/abilities/types';

// P9 (charter J/K): Skyborne Flight on Earth from the Sol start, driven only
// through player inputs (real key events, the test API's injected keys and
// presses); power state is read through the PLAYER hooks, never set. Exit
// down the ladder; Q does nothing on Earth (its only power is flight). Take
// off beside the ladder: E is refused while flying ("land first"); land, and E
// boards up the ladder; exit again. Take off from a jump, climb, cruise,
// boost, then dive at the ground at full speed: the flier skims it and never
// passes through; climb and hover. Save while hovering and reload (leaving
// asks first while flying): the flight resumes as a hover where it was, and
// lands only on touchdown.

test.use({ viewport: { width: 640, height: 360 } });

const P = (ABILITIES['skyborne-flight'] as { params: FlightParams }).params;

test('Skyborne Flight on Earth: E refused in the air, boarding after landing, boost and a dive at the ground, hover, reload mid-flight, landing', async ({ page }) => {
  test.setTimeout(60 * 60 * 1000);
  const errors = collectErrors(page);
  await stubPointerLock(page);
  await bootToTitle(page, '?preset=low&system=sol');
  await api(page, 'setRenderEvery', 4);
  await page.click('#btn-new');
  await until(page, 's.state === "playing" && s.mode === "LANDED" && s.body === "earth"', 900_000);

  // Exit down the ladder; the power is Earth's own and ready.
  let r = await exitShip(page);
  expect(r.p.ability).toMatchObject({ state: 'walk', power: 'skyborne-flight', body: 'earth' });
  expect(r.a).toMatchObject({ id: 'skyborne-flight', state: 'walk', active: false });
  expect(r.w.primitive).toBe('flight');
  // Q is no power here.
  await page.keyboard.press('KeyQ');
  await holdFor(page, [], 0.5);
  expect(await transitions(page)).toEqual([]);

  // Take off beside the ladder: E is refused while flying, the walker stays out.
  await holdFor(page, ['Space'], P.takeoffHold + 0.3);
  r = await untilPower(page, 'a && a.state === "flight"', 60_000);
  await page.keyboard.press('KeyE');
  r = await untilPower(page, 'p && p.ability && p.ability.lastRefusal === "land first"', 30_000);
  expect(r.a.state).toBe('flight');
  expect((await snap(page)).mode).toBe('ON_FOOT');
  // Land; then E boards up the ladder, and exit again.
  await api(page, 'hold', 'ControlLeft', true);
  await untilPower(page, 'a && a.state === "walk"', 300_000);
  await api(page, 'hold', 'ControlLeft', false);
  await holdFor(page, [], 0.5);
  await page.keyboard.press('KeyE');
  await untilPower(page, 'p && p.avatar && p.avatar.state === "climb"', 60_000);
  await until(page, 's.mode === "LANDED"', 120_000);
  await holdFor(page, [], 1);
  r = await exitShip(page);
  expect(await transitions(page)).toEqual(['walk>flight', 'flight>walk']);

  // Take off from a jump (Space pressed, then held) and climb.
  await api(page, 'press', 'Space');
  const climb = await holdFor(page, ['Space'], P.takeoffHold + 4);
  r = await untilPower(page, 'a && a.state === "flight"', 60_000);
  expect(await transitions(page)).toEqual(['walk>flight', 'flight>walk', 'walk>flight']);
  expect(Math.max(...climb.map((w) => w.height ?? 0))).toBeGreaterThan(15);

  // Cruise, then boost: the setpoint reaches boost; the speed flown is the
  // setpoint or the loaded-collision limit, whichever is lower.
  await holdFor(page, ['KeyW'], 3);
  const boost = await holdFor(page, ['KeyW', 'ShiftLeft'], 9);
  const top = boost.at(-1)!;
  console.log(`boost: setpoint ${top.setpoint.toFixed(0)} m/s, limit ${top.limit === null ? 'none' : top.limit.toFixed(0)}, speed ${top.speed.toFixed(0)} m/s, height ${top.height?.toFixed(1)} m`);
  expect(top.setpoint).toBeGreaterThan(P.boost * 0.95);
  expect(top.speed).toBeGreaterThan(Math.min(P.boost, top.limit ?? Infinity) * 0.85);

  // Dive at the ground at full speed (Ctrl descends), however high the boost
  // left the flier, then skim it for 4 s: the flier comes down to skim it and
  // follows it; it never passes through (ray and analytic surface) and does
  // not land at speed.
  const isLow = (w: Record<string, any>) => w.height !== null && w.height < 3;
  const dive = await holdUntil(page, ['KeyW', 'ShiftLeft', 'ControlLeft'], (rows) => rows.filter(isLow).length >= 40, 120, 0.1);
  const minRay = Math.min(...dive.map((w) => (w.height === null ? Infinity : w.height)));
  const minSurface = Math.min(...dive.map((w) => w.terrainClearance));
  const low = dive.filter(isLow);
  console.log(`dive: ${dive.length} samples, ${low.length} within 3 m of the ground at up to ${Math.max(...low.map((w) => w.speed)).toFixed(0)} m/s; min ray height ${minRay.toFixed(2)} m, min clearance above the analytic surface ${minSurface.toFixed(2)} m`);
  expect(low.length).toBeGreaterThanOrEqual(40);
  expect(Math.max(...low.map((w) => w.speed))).toBeGreaterThan(60);
  expect(minRay).toBeGreaterThan(0);
  expect(minSurface).toBeGreaterThan(-0.5);
  expect(dive.every((w) => w.state === 'flight')).toBe(true);

  // Climb away and brake to a hover high up.
  await holdFor(page, ['Space'], 5);
  await holdFor(page, ['KeyX'], 6);
  r = await untilPower(page, 'w && w.state === "flight" && w.speed < 1', 120_000);
  const hover = r.w;
  expect(hover.height).toBeGreaterThan(P.landHeight + 5);

  // Save while hovering and reload: leaving asks first while flying.
  const dialogs: string[] = [];
  page.on('dialog', (d) => {
    dialogs.push(d.type());
    void d.accept();
  });
  await page.keyboard.press('Escape');
  await until(page, 's.state === "paused"', 30_000);
  const before = (await api(page, 'saveState')).latest?.savedAt ?? null;
  await page.click('#btn-save');
  await page.waitForFunction((b) => {
    const st = (window as any).__meridian.saveState();
    return st.latest && st.latest.valid && st.latest.savedAt !== b;
  }, before, { timeout: 60_000 });
  const heightSaved = (await power(page)).height as number;
  await page.reload();
  await page.waitForFunction(() => (window as any).__meridianBooted === true, null, { timeout: 300_000 });
  expect(dialogs).toContain('beforeunload');
  await api(page, 'setRenderEvery', 4);
  await page.click('#btn-continue');
  await until(page, 's.state === "playing" && s.mode === "ON_FOOT" && s.body === "earth"', 900_000);
  // Resumed as a hover where it was saved: flying, not falling, at the saved height.
  r = await untilPower(page, 'a && a.state === "flight" && w && w.state === "flight"', 120_000);
  await holdFor(page, [], 2);
  const resumed = await power(page);
  console.log(`reload: saved at ${heightSaved.toFixed(1)} m, resumed at ${resumed.height?.toFixed(1)} m, speed ${resumed.speed.toFixed(2)} m/s`);
  expect(resumed.state).toBe('flight');
  expect(Math.abs((resumed.height ?? 0) - heightSaved)).toBeLessThan(2);
  expect(resumed.speed).toBeLessThan(2);

  // Descend and land: the hand-back comes only on touchdown.
  await api(page, 'hold', 'ControlLeft', true);
  r = await untilPower(page, 'a && a.state === "walk"', 300_000);
  await api(page, 'hold', 'ControlLeft', false);
  expect(r.w.height).toBeLessThan(0.3);
  expect((await transitions(page)).at(-1)).toBe('flight>walk');

  console.log(`log: ${(await transitions(page)).join(', ')}`);
  expect(errors).toEqual([]);
});
