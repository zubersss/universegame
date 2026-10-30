import { expect, test, type Page } from '@playwright/test';
import { fileURLToPath } from 'node:url';
import { createServer, type ViteDevServer } from 'vite';
import { collectErrors } from '../helpers';

// W4 browser check: the data-backed Earth renders through the game's own
// terrain, proxy, atmosphere and sky modules (worlds-lab.html on a Vite dev
// server started here, because Earth is not yet on the travel route). Views:
// ground level over New Zealand's Southern Alps (Tasman coast to Aoraki, from
// the regional 10" grid), the coarse terrain from 2.2 radii, and the distant
// proxy from 4.5 radii. Screenshots go to evidence/worlds-earth-*.png.

test.use({ viewport: { width: 960, height: 540 } });

const root = fileURLToPath(new URL('../../', import.meta.url));
let server: ViteDevServer;
let base = '';

test.beforeAll(async () => {
  // No HMR: a source edit during a run must not reload the page under the test.
  server = await createServer({ root, configFile: `${root}vite.config.ts`, logLevel: 'error', server: { port: 5181, strictPort: false, host: '127.0.0.1', hmr: false } });
  await server.listen();
  base = server.resolvedUrls!.local[0];
});

test.afterAll(async () => {
  await server?.close();
});

interface Lab {
  ready: boolean;
  settled: boolean;
  frames: number;
  errors: string[];
  stats: Record<string, number>;
  pixels: { mean: number; std: number; blue: number; land: number; surface: number } | null;
}

async function view(page: Page, query: string, shot: string, settleMs = 900_000): Promise<Lab> {
  await page.goto(`${base}e2e/journey/worlds-lab.html?${query}`);
  await page.waitForFunction(() => (window as any).__lab?.ready === true || (window as any).__lab?.errors.length > 0, null, { timeout: 300_000 });
  await page.waitForFunction(() => (window as any).__lab?.settled === true || (window as any).__lab?.errors.length > 0, null, { timeout: settleMs, polling: 500 });
  await page.evaluate(() => { (window as any).__lab.requestPixels = true; });
  await page.waitForFunction(() => (window as any).__lab?.pixels != null, null, { timeout: 120_000 });
  const lab = (await page.evaluate(() => (window as any).__lab)) as Lab;
  await page.screenshot({ path: `${root}evidence/${shot}` });
  console.log(shot, JSON.stringify({ stats: lab.stats, pixels: lab.pixels, frames: lab.frames }));
  return lab;
}

test('Earth: ground, coarse terrain and proxy views render from the data', async ({ page }) => {
  test.setTimeout(45 * 60 * 1000);
  const errors = collectErrors(page);

  // 1. Ground level: 1.2 km above the Tasman Sea off the West Coast, looking east-southeast at the Alps.
  const ground = await view(page, 'body=earth&lat=-43.30&lon=169.80&alt=1200&heading=115&pitch=4&fov=60', 'worlds-earth-southern-alps.png');
  expect(ground.errors).toEqual([]);
  expect(ground.stats.rendered).toBeGreaterThan(40);
  expect(ground.stats.maxLevel).toBeGreaterThanOrEqual(8); // ~1 km chunks at 1.2 km altitude
  expect(ground.stats.errors).toBe(0);
  expect(ground.pixels!.std).toBeGreaterThan(8); // not a flat fill
  expect(ground.pixels!.surface).toBeGreaterThan(0.25); // terrain covers the lower part of the frame

  // 2. Coarse terrain from 2.2 radii over the Tasman Sea (Australia and New Zealand in daylight).
  const coarse = await view(page, 'body=earth&lat=-35&lon=160&orbit=2.2&fov=50', 'worlds-earth-orbit-terrain.png');
  expect(coarse.errors).toEqual([]);
  expect(coarse.stats.rendered).toBeGreaterThan(5);
  expect(coarse.pixels!.blue).toBeGreaterThan(0.02); // ocean visible
  expect(coarse.pixels!.land).toBeGreaterThan(0.005); // continents visible
  expect(coarse.pixels!.surface).toBeGreaterThan(0.3); // the globe is local terrain at 2.2 radii

  // 3. Distant proxy from 4.5 radii (terrain released, proxy only).
  const proxy = await view(page, 'body=earth&lat=-35&lon=160&orbit=4.5&fov=50', 'worlds-earth-orbit-proxy.png');
  expect(proxy.errors).toEqual([]);
  expect(proxy.stats.proxies).toBe(1);
  expect(proxy.pixels!.mean).toBeGreaterThan(3);
  expect(proxy.pixels!.surface).toBe(0); // terrain released: only the proxy draws the planet

  expect(errors).toEqual([]);
});
