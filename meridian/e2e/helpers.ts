import { expect, type Page } from '@playwright/test';

export type Snapshot = Record<string, any>;

export function collectErrors(page: Page): string[] {
  const errors: string[] = [];
  page.on('console', (m) => {
    if (m.type() === 'error') errors.push(`console.error: ${m.text()}`);
  });
  page.on('pageerror', (e) => errors.push(`pageerror: ${e.message}`));
  page.on('requestfailed', (r) => errors.push(`requestfailed: ${r.url()} ${r.failure()?.errorText ?? ''}`));
  return errors;
}

/**
 * Long journeys only: make pointer-lock requests succeed without locking.
 * Headless Chromium's renderer memory grows steadily while the pointer is
 * locked (measured in PROGRESS.md, Phase 8), which crashed hour-long runs.
 * The game never reads the lock state except for mouse deltas, and the test
 * autopilot injects look input directly, so behaviour is otherwise unchanged.
 * The production smoke and the shorter specs keep the real lock.
 */
export async function stubPointerLock(page: Page): Promise<void> {
  await page.addInitScript(() => {
    Element.prototype.requestPointerLock = function () {
      return Promise.resolve();
    } as typeof Element.prototype.requestPointerLock;
  });
}

export async function bootToTitle(page: Page, query = ''): Promise<void> {
  await page.goto(`./${query}`);
  await page.waitForFunction(() => (window as any).__meridianBooted === true, null, { timeout: 180_000 });
  await expect(page.locator('#btn-new')).toBeEnabled();
}

export async function snap(page: Page): Promise<Snapshot> {
  return page.evaluate(() => (window as any).__meridian.snapshot());
}

/** Wait until simulation time advanced by `seconds` (sim time, not wall time). */
export async function waitSim(page: Page, seconds: number, timeoutMs = 900_000): Promise<Snapshot> {
  const t0 = (await snap(page)).simTime as number;
  await page.waitForFunction((t) => (window as any).__meridian.snapshot().simTime >= t, t0 + seconds, {
    timeout: timeoutMs,
    polling: 250,
  });
  return snap(page);
}

/** Wait (in sim time) until a predicate over the snapshot holds. */
export async function waitUntil(page: Page, fnSrc: string, timeoutMs = 900_000): Promise<Snapshot> {
  await page.waitForFunction(
    (src) => {
      const s = (window as any).__meridian.snapshot();
      return new Function('s', `return (${src});`)(s);
    },
    fnSrc,
    { timeout: timeoutMs, polling: 250 },
  );
  return snap(page);
}

/** Hold a key via real keyboard events for a span of simulation time. */
export async function holdKey(page: Page, key: string, simSeconds: number): Promise<Snapshot> {
  await page.keyboard.down(key);
  const s = await waitSim(page, simSeconds);
  await page.keyboard.up(key);
  return s;
}

export function finite(s: Snapshot): boolean {
  const nums = [...(s.shipSystem as number[]), ...(s.vel as number[]), ...(s.quat as number[]), s.speed as number];
  return nums.every((x) => Number.isFinite(x));
}

/** Angle (rad) between two quaternions. */
export function quatAngle(a: number[], b: number[]): number {
  const d = Math.abs(a[0] * b[0] + a[1] * b[1] + a[2] * b[2] + a[3] * b[3]);
  return 2 * Math.acos(Math.min(1, d));
}
