import { expect, test } from '@playwright/test';
import { collectErrors } from '../helpers';

// Production build (dist/) smoke test through the DOM only: no test API is
// present. Real clicks and key events; checks rendering, flight start, pause,
// navigation panel, resize, and the absence of console/page/request errors.

test.use({ viewport: { width: 800, height: 450 } });

test('production build boots, plays, pauses and opens navigation', async ({ page }) => {
  test.setTimeout(20 * 60 * 1000);
  const errors = collectErrors(page);
  const requests: string[] = [];
  page.on('request', (r) => requests.push(r.url()));
  await page.goto('./?preset=low');
  await expect(page.locator('#btn-new')).toBeEnabled({ timeout: 180_000 });
  expect(await page.evaluate(() => typeof (window as any).__meridian)).toBe('undefined');

  await page.click('#btn-new');
  await expect(page.locator('#hud')).toBeVisible({ timeout: 600_000 });
  await expect(page.locator('#screen-loading')).toBeHidden({ timeout: 600_000 });
  await expect(page.locator('#hud-mode')).toHaveText(/Landed/i);
  // Small viewport: the location reads from the instrument panel header.
  await expect(page.locator('#flight-panel .panel-loc')).toBeVisible();
  await expect(page.locator('#flight-panel .panel-loc')).toHaveText(/Ilex · Landed/i);

  // Non-blank render: the canvas has real variation.
  const shot = await page.locator('#view').screenshot({ timeout: 180_000 });
  expect(shot.length).toBeGreaterThan(20_000);

  // Take off with Space and climb a little.
  await page.keyboard.press('Space');
  await page.keyboard.down('Space');
  await expect(page.locator('#hud-mode')).toHaveText(/Flight/i, { timeout: 60_000 });
  await page.waitForTimeout(4000);
  await page.keyboard.up('Space');
  const speed = Number((await page.locator('#i-speed').textContent()) ?? '0');
  expect(speed).toBeGreaterThanOrEqual(0);

  // Navigation panel.
  await page.keyboard.press('Tab');
  await expect(page.locator('#panel-nav')).toBeVisible();
  await expect(page.locator('#nav-list .navrow')).toHaveCount(3);
  await page.keyboard.press('Digit2');
  await expect(page.locator('#nav-list .navrow.selected')).toHaveCount(1);
  await page.keyboard.press('Tab');
  await expect(page.locator('#panel-nav')).toBeHidden();
  await expect(page.locator('#hud')).toBeVisible();
  // Reopen and close with the button.
  await page.keyboard.press('Tab');
  await expect(page.locator('#panel-nav')).toBeVisible();
  await page.click('#btn-panel-close');
  await expect(page.locator('#panel-nav')).toBeHidden();

  // Pause and resume.
  await page.keyboard.press('Escape');
  await expect(page.locator('#screen-pause')).toBeVisible();
  await page.click('#btn-resume');
  await expect(page.locator('#screen-pause')).toBeHidden();

  // Resize keeps rendering.
  await page.setViewportSize({ width: 1024, height: 576 });
  await page.waitForTimeout(1500);
  const box = await page.locator('#view').boundingBox();
  expect(box?.width).toBe(1024);
  await page.screenshot({ path: 'evidence/phase8-prod-smoke.png', timeout: 180_000 });

  expect(requests.some((u) => /testHooks|autopilot/i.test(u))).toBe(false);
  // No runtime hotlinks: every request stays on the serving origin.
  const origin = new URL(page.url()).origin;
  expect(requests.filter((u) => !u.startsWith(origin + '/') && !u.startsWith('data:') && !u.startsWith('blob:'))).toEqual([]);
  expect(requests.length).toBeGreaterThan(2);
  expect(errors).toEqual([]);
});
