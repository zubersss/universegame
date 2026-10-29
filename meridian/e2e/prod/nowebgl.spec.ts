import { expect, test } from '@playwright/test';

// A browser without WebGL 2 gets the compatibility message instead of a broken
// page (production build, WebGL disabled at browser launch).

test.use({ launchOptions: { args: ['--disable-webgl', '--disable-webgl2'] } });

test('shows the WebGL 2 compatibility message', async ({ page }) => {
  test.setTimeout(5 * 60 * 1000);
  await page.goto('./');
  await expect(page.locator('#screen-error')).toBeVisible({ timeout: 120_000 });
  await expect(page.locator('#error-title')).toHaveText('WebGL 2 is required');
  await expect(page.locator('#error-text')).toContainText('WebGL 2');
  await expect(page.locator('#btn-new')).toBeHidden();
  await page.screenshot({ path: 'evidence/phase8-no-webgl2.png' });
});
