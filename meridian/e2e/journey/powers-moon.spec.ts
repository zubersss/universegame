import { expect, test } from '@playwright/test';
import { bootToTitle, collectErrors, snap, stubPointerLock } from '../helpers';
import { api, exitShip, holdFor, importFixture, look, power, transitions, until, untilPower } from '../fixtures/powers';
import { ABILITIES } from '../../src/abilities/catalog';
import type { BlinkParams } from '../../src/abilities/types';

// P9 (charter J/K): Lunar Step on the Moon, from a landed save: the fixture
// e2e/fixtures/moon-landed.json is a real backup exported after flying there
// from the Sol start (regenerate it with `node e2e/fixtures/regenerate.mjs`
// when its import fails). Driven only through player inputs; power state is
// read through the PLAYER hooks. Space only jumps here (flight, unlocked on
// Earth, is Earth's power); an aimed step lands on the ground under the aim
// within range; a second one during the cooldown is refused and consumes
// nothing; aiming at the sky is refused; Q steps without aiming; a step aimed
// at the ship never ends inside it; after a save and reload the power works.

test.use({ viewport: { width: 640, height: 360 } });

const P = (ABILITIES['lunar-step'] as { params: BlinkParams }).params;

test('Lunar Step on the Moon: aimed and quick steps, cooldown and sky refusals, the ship as an obstacle, reload', async ({ page }) => {
  test.setTimeout(45 * 60 * 1000);
  const errors = collectErrors(page);
  await stubPointerLock(page);
  await bootToTitle(page, '?preset=low&system=sol');
  await api(page, 'setRenderEvery', 4);
  await importFixture(page, 'moon-landed.json', 'moon');
  let r = await exitShip(page);
  expect(r.p.ability).toMatchObject({ state: 'walk', power: 'lunar-step', body: 'moon' });
  // Flight is unlocked (on Earth) in this expedition, but it is Earth's power.
  expect(await page.evaluate(() => [...(window as any).__meridian.game.expedition.unlocked])).toContain('skyborne-flight');
  expect(r.w.primitive).toBe('blink');

  // Space (pressed and held) is a jump here, never flight.
  await api(page, 'press', 'Space');
  await holdFor(page, ['Space'], 1.5);
  await untilPower(page, 'w && w.grounded', 60_000);
  expect(await transitions(page)).toEqual([]);

  // Aim (right mouse held) at the ground ahead and step there with a click.
  await look(page, 0, 0.07);
  await api(page, 'hold', 'MouseRight', true);
  r = await untilPower(page, 'w && w.aiming && w.target.ok', 60_000);
  const target = r.w.target;
  expect(target.distance).toBeGreaterThan(5);
  expect(target.distance).toBeLessThanOrEqual(P.range);
  const s0 = await snap(page);
  await api(page, 'press', 'MouseLeft');
  r = await untilPower(page, 'w && w.jumps === 1', 30_000);
  const s1 = await snap(page);
  const moved = Math.hypot(...(s1.player.system as number[]).map((v: number, i: number) => v - s0.player.system[i]));
  console.log(`aimed step: target ${target.distance.toFixed(1)} m, moved ${moved.toFixed(1)} m`);
  expect(Math.abs(moved - target.distance)).toBeLessThan(2);
  expect(r.w.clear).toBe(true);
  expect(await transitions(page)).toEqual(['walk>blink', 'blink>walk']);
  // A second click during the cooldown is refused and steps nowhere.
  await api(page, 'press', 'MouseLeft');
  r = await untilPower(page, 'w && w.refusal === "cooldown"', 30_000);
  expect(r.w.jumps).toBe(1);

  // After the cooldown, aiming at the sky is refused; nothing is consumed.
  await holdFor(page, [], P.cooldown + 0.3);
  await look(page, 0, -0.9);
  r = await untilPower(page, 'w && w.aiming && !w.target.ok', 60_000);
  console.log(`sky: ${r.w.target.reason}`);
  expect(['no target', 'out of range', 'no ground']).toContain(r.w.target.reason);
  await api(page, 'press', 'MouseLeft');
  r = await untilPower(page, 'w && w.refusal !== null', 30_000);
  expect(r.w.refusal).toBe(r.w.target.reason);
  expect(r.w.jumps).toBe(1);
  await api(page, 'hold', 'MouseRight', false);

  // Q steps along the look without holding right mouse.
  await look(page, 0, 0.9);
  await holdFor(page, [], 0.5);
  await api(page, 'press', 'KeyQ');
  r = await untilPower(page, 'w && w.jumps === 2', 30_000);
  expect(r.w.clear).toBe(true);

  // A step aimed at the ship: refused, or it ends clear of the hull (on it or
  // beside it), never inside.
  await holdFor(page, [], P.cooldown + 0.3);
  const ship = await page.evaluate(() => {
    const g = (window as any).__meridian.game;
    return g.ship.currPos.clone().sub(g.bodyCenterLocal).toArray();
  });
  await api(page, 'autopilot', { kind: 'aim', atPlanet: ship });
  await holdFor(page, [], 1);
  await api(page, 'autopilot', null);
  await api(page, 'hold', 'MouseRight', true);
  await holdFor(page, [], 0.3);
  const atShip = (await power(page)).target;
  await api(page, 'press', 'MouseLeft');
  await holdFor(page, [], 0.5);
  await api(page, 'hold', 'MouseRight', false);
  const after = await power(page);
  console.log(`step at the ship: ${atShip.ok ? `allowed (${atShip.distance.toFixed(1)} m)` : `refused (${atShip.reason})`}, jumps ${after.jumps}, clear ${after.clear}`);
  expect(after.clear).toBe(true);

  // Save on foot and reload: the power still steps.
  await page.keyboard.press('Escape');
  await until(page, 's.state === "paused"', 30_000);
  const before = (await api(page, 'saveState')).latest?.savedAt ?? null;
  await page.click('#btn-save');
  await page.waitForFunction((b) => {
    const st = (window as any).__meridian.saveState();
    return st.latest && st.latest.valid && st.latest.savedAt !== b;
  }, before, { timeout: 60_000 });
  await page.reload();
  await page.waitForFunction(() => (window as any).__meridianBooted === true, null, { timeout: 300_000 });
  await api(page, 'setRenderEvery', 4);
  await page.click('#btn-continue');
  await until(page, 's.state === "playing" && s.mode === "ON_FOOT" && s.body === "moon"', 900_000);
  r = await untilPower(page, 'a && a.id === "lunar-step" && a.state === "walk" && w', 120_000);
  await look(page, 0, 0.07);
  await api(page, 'hold', 'MouseRight', true);
  await untilPower(page, 'w && w.aiming && w.target.ok', 60_000);
  await api(page, 'press', 'MouseLeft');
  r = await untilPower(page, 'w && w.jumps === 1', 30_000);
  expect(r.w.clear).toBe(true);
  await api(page, 'hold', 'MouseRight', false);
  expect(errors).toEqual([]);
});
