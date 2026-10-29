import { expect, test } from '@playwright/test';
import { bootToTitle, collectErrors, finite, holdKey, quatAngle, snap, waitSim, waitUntil } from '../helpers';

// Phase 2 gate: a multi-minute flight through the real DOM input path
// (Playwright keyboard events), checking acceleration, pitch, yaw, roll,
// climb, boost, brake, hover, ground collision and pause/resume.

test.use({ viewport: { width: 640, height: 360 } });

test('flight test: controls, collision and pause/resume', async ({ page }) => {
  test.setTimeout(40 * 60 * 1000);
  const errors = collectErrors(page);
  await bootToTitle(page, '?preset=low');
  // Draw every 16th frame (software rendering); simulation rules are unchanged.
  await page.evaluate(() => (window as any).__meridian.setRenderEvery(16));
  await page.click('#btn-new');
  await expect(page.locator('#hud')).toBeVisible();
  const log: string[] = [];
  const note = (k: string, s: Record<string, any>) =>
    log.push(`${k}: t=${(+s.simTime).toFixed(1)} spd=${(+s.speed).toFixed(1)} clr=${(+s.clearance).toFixed(1)} alt=${(+s.altitude).toFixed(1)} thr=${(+s.throttle).toFixed(2)} vs=${(+s.verticalSpeed).toFixed(1)}`);

  let s = await waitUntil(page, 's.state === "playing"');
  expect(s.mode).toBe('LANDED');
  // Take off (Space) and climb to about 40 m, then let go and hover.
  await page.keyboard.press('Space');
  await page.keyboard.down('Space');
  s = await waitUntil(page, 's.mode === "PILOTING" && s.clearance > 38');
  await page.keyboard.up('Space');
  s = await waitSim(page, 3);
  // Altitude above the datum radius: what the flight model holds (ground height
  // varies under the ship once it moves).
  const hoverAlt = s.altitude as number;
  note('hover-start', s);
  const q0 = s.quat as number[];

  // Acceleration (W raises throttle).
  s = await holdKey(page, 'KeyW', 3);
  note('throttle-up', s);
  s = await waitSim(page, 3);
  note('accelerated', s);
  expect(s.throttle).toBeGreaterThan(0.9);
  expect(s.speed).toBeGreaterThan(60);
  expect(Math.abs(s.altitude - hoverAlt)).toBeLessThan(6); // holds altitude while accelerating
  expect(s.clearance).toBeGreaterThan(10);

  // Pitch up with the keyboard alternative (ArrowUp), then level.
  const before = s;
  s = await holdKey(page, 'ArrowUp', 1.2);
  s = await waitSim(page, 2);
  note('pitched', s);
  expect(s.altitude).toBeGreaterThan(before.altitude + 3);

  // Yaw (D) and roll (E) rotate the ship.
  const qa = s.quat as number[];
  s = await holdKey(page, 'KeyD', 1.5);
  const yawAngle = quatAngle(qa, s.quat);
  expect(yawAngle).toBeGreaterThan(0.4);
  const qb = s.quat as number[];
  s = await holdKey(page, 'KeyE', 0.8);
  expect(quatAngle(qb, s.quat)).toBeGreaterThan(0.3);
  note('yaw-roll', s);
  expect(quatAngle(q0, s.quat)).toBeGreaterThan(0.5);
  // Auto-level returns bank toward level once roll input is released.
  s = await waitSim(page, 4);

  // Climb above 1,000 m clearance (Space), then boost (Shift) raises speed past the normal cap.
  await page.keyboard.down('Space');
  s = await waitUntil(page, 's.clearance > 1150');
  await page.keyboard.up('Space');
  note('climbed', s);
  await page.keyboard.down('ShiftLeft');
  s = await waitSim(page, 6);
  note('boost', s);
  expect(s.boost).toBe(true);
  expect(s.speed).toBeGreaterThan(355); // atmospheric cap without boost is 350
  await page.keyboard.up('ShiftLeft');

  // Brake (X) to a full stop, then hover with no input.
  await page.keyboard.down('KeyX');
  s = await waitUntil(page, 's.speed < 2');
  await page.keyboard.up('KeyX');
  note('braked', s);
  expect(s.throttle).toBe(0);
  const hoverStart = s;
  s = await waitSim(page, 3);
  note('hover', s);
  expect(s.speed).toBeLessThan(1.5);
  expect(Math.abs(s.altitude - hoverStart.altitude)).toBeLessThan(3);

  // Collision: descend (Ctrl) all the way down and push into the ground.
  await page.keyboard.down('ControlLeft');
  s = await waitUntil(page, 's.clearance < 4', 1_500_000);
  s = await waitSim(page, 4);
  await page.keyboard.up('ControlLeft');
  note(`ground (${s.mode})`, s);
  expect(finite(s)).toBe(true);
  expect(s.clearance).toBeGreaterThan(0.5); // resting on hull/gear, not through the ground
  expect(s.speed).toBeLessThan(5);

  // Pause/resume: Escape pauses (sim time frozen), Resume restores input.
  await page.keyboard.press('Escape');
  await expect(page.locator('#screen-pause')).toBeVisible();
  const p0 = (await snap(page)).simTime;
  await page.waitForTimeout(2500);
  const p1 = (await snap(page)).simTime;
  expect(p1).toBe(p0);
  await page.click('#btn-resume');
  await expect(page.locator('#screen-pause')).toBeHidden();
  // Resting on the gear after the descent settles the ship as LANDED: take off
  // again (Space) before throttling up, as a player would.
  if ((await snap(page)).mode === 'LANDED') {
    await page.keyboard.press('Space');
    await waitUntil(page, 's.mode === "PILOTING" && s.clearance > 5', 300_000);
  }
  s = await holdKey(page, 'KeyW', 2);
  s = await waitSim(page, 2);
  note('after-resume', s);
  expect(s.throttle).toBeGreaterThan(0.5);
  expect(s.speed).toBeGreaterThan(20);
  expect(finite(s)).toBe(true);

  await page.screenshot({ path: 'evidence/phase2-flight-test-end.png' });
  console.log(log.join('\n'));
  console.log(`steps dropped by the frame cap: ${s.droppedSteps}, frames: ${s.frame}`);
  expect(errors).toEqual([]);
});
