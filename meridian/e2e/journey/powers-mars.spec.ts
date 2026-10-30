import { expect, test, type Page } from '@playwright/test';
import { bootToTitle, collectErrors, stubPointerLock } from '../helpers';
import { api, exitShip, hook, holdFor, importFixture, power, transitions, until, untilPower, type Row } from '../fixtures/powers';
import { ABILITIES } from '../../src/abilities/catalog';
import { SPEED_EXIT_MAX, type SpeedParams } from '../../src/abilities/types';
import { STOP_MARGIN } from '../../src/abilities/speed';

// P9 (charter J/K): Redline on Mars, from a landed save (fixture
// e2e/fixtures/mars-landed.json, a real backup exported after flying there
// from the Sol start; regenerate it with `node e2e/fixtures/regenerate.mjs`
// when its import fails), with frames capped at 30 fps (a 30 Hz display).
// Driven only through player inputs; power state read through the PLAYER
// hooks. Space only jumps here; Q runs and releasing it always brakes, at the
// brake rate, down to walking; run back at the ship at full speed: the
// braking curve stops short of the hull with no contact; save mid-run and
// reload: the run resumes braking and hands back to walking.

test.use({ viewport: { width: 640, height: 360 } });

const P = (ABILITIES.redline as { params: SpeedParams }).params;
/** Largest speed drop between samples 0.1 s apart while braking (the brake rate, with one step of sampling slack). */
const DROP_MAX = P.brake * (0.1 + 1 / 60) + 0.5;

/** Turn the explorer toward a point (relative to the body's centre) with the autopilot's mouse look. */
async function face(page: Page, atPlanet: number[]): Promise<void> {
  await api(page, 'autopilot', { kind: 'aim', atPlanet });
  await holdFor(page, [], 1);
  await api(page, 'autopilot', null);
}

/**
 * Largest speed drop between consecutive samples braking for the given
 * hazard kinds (null: plain braking, no hazard ahead), above sprint speed.
 * Unloaded collision ahead is not judged here: WORLDS' corridor still leaves
 * holes that limit speed (reported, see the log line).
 */
const maxBrakeDrop = (rows: Row[], kinds: (string | null)[]) => {
  let m = 0;
  for (let i = 1; i < rows.length; i++) {
    if (rows[i - 1].run > SPEED_EXIT_MAX && kinds.includes(rows[i].obstacleKind)) m = Math.max(m, rows[i - 1].run - rows[i].run);
  }
  return m;
};
/** Samples limited by collision not loaded ahead (WORLDS' corridor), for the log. */
const unloaded = (rows: Row[]) => rows.filter((w) => w.obstacleKind === 'unloaded').length;

test('Redline on Mars at 30 fps: run and brake, a full-speed run at the ship stops short of it, reload mid-run', async ({ page }) => {
  test.setTimeout(45 * 60 * 1000);
  const errors = collectErrors(page);
  await stubPointerLock(page);
  // A 30 Hz display: the game's frame callbacks come at most 30 times a second.
  await page.addInitScript(() => {
    const raf = window.requestAnimationFrame.bind(window);
    let last = -Infinity;
    window.requestAnimationFrame = (cb) =>
      raf(function tick(t) {
        if (t - last >= 1000 / 30 - 2) {
          last = t;
          cb(t);
        } else raf(tick);
      });
  });
  await bootToTitle(page, '?preset=low&system=sol');
  await api(page, 'setRenderEvery', 2);
  await importFixture(page, 'mars-landed.json', 'mars');
  let r = await exitShip(page);
  expect(r.p.ability).toMatchObject({ state: 'walk', power: 'redline', body: 'mars' });
  expect(r.w.primitive).toBe('speed');

  // Space (pressed and held) is a jump here, never flight.
  await api(page, 'press', 'Space');
  await holdFor(page, ['Space'], 1.5);
  await untilPower(page, 'w && w.grounded', 60_000);
  expect(await transitions(page)).toEqual([]);

  // Run straight away from the ship, then release Q: braking at the brake rate down to walking.
  const geo = await page.evaluate(() => {
    const g = (window as any).__meridian.game;
    const ship = g.ship.currPos.clone().sub(g.bodyCenterLocal);
    const me = g.player.pos.clone().sub(g.bodyCenterLocal);
    const away = me.clone().sub(ship);
    away.addScaledVector(me.clone().normalize(), -away.dot(me.clone().normalize())).normalize();
    return { ship: ship.toArray(), away: me.clone().addScaledVector(away, 800).toArray() };
  });
  await face(page, geo.away);
  const out = await holdFor(page, ['KeyQ'], 4.5, 0.1);
  const brake = await holdFor(page, [], 4, 0.1);
  r = await untilPower(page, 'a && a.state === "walk"', 60_000);
  const top = Math.max(...out.map((w) => w.run));
  console.log(`run out: top ${top.toFixed(1)} m/s (${unloaded(out)} of ${out.length} samples limited by unloaded collision); braking drop max ${maxBrakeDrop(brake, [null]).toFixed(2)} m/s per 0.1 s; ship gap ${(await hook(page, 'shipGap')).toFixed(0)} m`);
  expect(top).toBeGreaterThan(60);
  expect(brake.some((w) => w.braking)).toBe(true);
  expect(maxBrakeDrop(brake, [null])).toBeLessThanOrEqual(DROP_MAX);
  expect(await transitions(page)).toEqual(['walk>speed', 'speed>walk']);

  // Turn around and run back at the ship at full speed, Q held throughout:
  // the hull is seen ahead and the braking curve stops the runner short of it.
  await face(page, geo.ship);
  const back: Row[] = [];
  const gaps: number[] = [];
  await api(page, 'hold', 'KeyQ', true);
  for (let i = 0; i < 400; i++) {
    const w = (await holdFor(page, [], 0.1, 0.1))[0];
    back.push(w);
    gaps.push(await hook(page, 'shipGap'));
    if (i > 20 && w.run < 0.5 && back[i - 5].run < 0.5) break;
  }
  await api(page, 'hold', 'KeyQ', false);
  const peak = Math.max(...back.map((w) => w.run));
  const walls = back.filter((w) => w.obstacleKind === 'wall');
  const minGap = Math.min(...gaps);
  console.log(`run back: peak ${peak.toFixed(1)} m/s, ${walls.length} samples braking for the hull (${unloaded(back)} limited by unloaded collision), braking drop max ${maxBrakeDrop(back, ['wall']).toFixed(2)} m/s per 0.1 s, closest ${minGap.toFixed(2)} m, contact ${back.some((w) => w.hitWall)}`);
  expect(peak).toBeGreaterThan(60);
  expect(walls.length).toBeGreaterThan(5);
  expect(back.some((w) => w.hitWall)).toBe(false);
  expect(minGap).toBeGreaterThan(0.2);
  expect(minGap).toBeLessThan(STOP_MARGIN + 6);
  expect(maxBrakeDrop(back, ['wall'])).toBeLessThanOrEqual(DROP_MAX);
  expect(back.every((w) => w.clear)).toBe(true);
  // Q released at rest: hands back to walking.
  await untilPower(page, 'a && a.state === "walk"', 60_000);

  // Save mid-run and reload: the run resumes braking, then walks.
  await face(page, geo.away);
  await api(page, 'hold', 'KeyQ', true);
  await holdFor(page, [], 2);
  await page.keyboard.press('Escape');
  await until(page, 's.state === "paused"', 30_000);
  await api(page, 'hold', 'KeyQ', false);
  expect((await power(page)).state).toBe('speed');
  const before = (await api(page, 'saveState')).latest?.savedAt ?? null;
  await page.click('#btn-save');
  await page.waitForFunction((b) => {
    const st = (window as any).__meridian.saveState();
    return st.latest && st.latest.valid && st.latest.savedAt !== b;
  }, before, { timeout: 60_000 });
  await page.reload();
  await page.waitForFunction(() => (window as any).__meridianBooted === true, null, { timeout: 300_000 });
  await api(page, 'setRenderEvery', 2);
  await page.click('#btn-continue');
  await until(page, 's.state === "playing" && s.mode === "ON_FOOT" && s.body === "mars"', 900_000);
  // Resumed braking (a save keeps no speed, so from rest), then walking.
  await page.waitForFunction(() => {
    const l = (window as any).__meridian.player.abilityLog() as { from: string; to: string }[];
    return l.some((e) => e.to === 'speed') && l[l.length - 1].to === 'walk';
  }, null, { timeout: 120_000, polling: 200 });
  const log = await transitions(page);
  console.log(`after reload: ${log.join(', ')}`);
  expect(log).toContain('walk>speed');
  expect(log.at(-1)).toBe('speed>walk');
  const fr = (await api(page, 'perf')).frames as Row;
  console.log(`frames: ${JSON.stringify(fr)}`);
  expect(errors).toEqual([]);
});
