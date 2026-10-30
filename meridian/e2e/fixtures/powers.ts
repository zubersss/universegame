import { expect, type Page } from '@playwright/test';
import { fileURLToPath } from 'node:url';
import { snap } from '../helpers';

// Shared steps of the power journeys (e2e/journey/powers-*.spec.ts). They
// drive the game only through player inputs (the test API's injected keys,
// mouse look and presses) and read state through the PLAYER hooks.

export type Row = Record<string, any>;

export const api = (page: Page, fn: string, ...args: unknown[]): Promise<any> =>
  page.evaluate(([f, a]) => (window as any).__meridian[f as string](...(a as unknown[])), [fn, args] as const);
export const hook = (page: Page, fn: string, ...args: unknown[]): Promise<any> =>
  page.evaluate(([f, a]) => (window as any).__meridian.player[f as string](...(a as unknown[])), [fn, args] as const);
/** The active power's motion and checks (player.power()). */
export const power = (page: Page): Promise<Row> => hook(page, 'power');

/** Wait until a predicate over the snapshot `s` holds; returns the snapshot. */
export async function until(page: Page, src: string, timeoutMs = 600_000): Promise<Row> {
  await page.waitForFunction((c) => new Function('s', `return (${c});`)((window as any).__meridian.snapshot()), src, { timeout: timeoutMs, polling: 300 });
  return snap(page);
}

/** Wait until a predicate over p = player.state(), w = player.power(), a = player.ability() holds; returns them as read then. */
export async function untilPower(page: Page, src: string, timeoutMs = 600_000): Promise<Row> {
  const h = await page.waitForFunction(
    (c) => {
      const m = (window as any).__meridian.player;
      const r = { p: m.state(), w: m.power(), a: m.ability() };
      return new Function('p', 'w', 'a', `return (${c});`)(r.p, r.w, r.a) ? r : null;
    },
    src,
    { timeout: timeoutMs, polling: 200 },
  );
  return (await h.jsonValue()) as Row;
}

/** Hold keys (or mouse buttons) for `seconds` of simulation time, sampling the power every `every` s. */
export async function holdFor(page: Page, keys: string[], seconds: number, every = 0.2): Promise<Row[]> {
  for (const k of keys) await api(page, 'hold', k, true);
  const t0 = (await snap(page)).simTime as number;
  const out: Row[] = [];
  for (let t = t0 + every; t <= t0 + seconds + 1e-9; t += every) {
    await page.waitForFunction((tt) => (window as any).__meridian.snapshot().simTime >= tt, t, { timeout: 600_000, polling: 50 });
    out.push(await power(page));
  }
  for (const k of keys) await api(page, 'hold', k, false);
  return out;
}

/** The ability state changes so far, as 'from>to'. */
export const transitions = async (page: Page): Promise<string[]> => ((await hook(page, 'abilityLog')) as { from: string; to: string }[]).map((e) => `${e.from}>${e.to}`);

/** Mouse look in radians (positive pitch looks down), as the game reads mouse motion at the default sensitivity. */
export const look = (page: Page, yaw: number, pitchDown: number) => api(page, 'mouse', yaw / 0.0022, pitchDown / 0.0022);

/**
 * Import a landed-save fixture from the title screen and wait until the game
 * plays it; a failed import fails the journey with what to do about it.
 */
export async function importFixture(page: Page, name: string, body: string): Promise<Row> {
  const file = fileURLToPath(new URL(`./${name}`, import.meta.url));
  await page.setInputFiles('#file-import', file);
  try {
    return await until(page, `s.state === "playing" && s.mode === "LANDED" && s.body === "${body}" && s.bodyShown`, 900_000);
  } catch (e) {
    const note = await page.locator('#title-save-note').textContent().catch(() => null);
    expect(null, `importing e2e/fixtures/${name} failed (${note ?? String(e)}): regenerate fixture with node e2e/fixtures/regenerate.mjs`).not.toBeNull();
    throw e;
  }
}

/** Exit the ship down the ladder; returns when the climb is over and the explorer stands at its foot. */
export async function exitShip(page: Page): Promise<Row> {
  await page.keyboard.press('KeyE');
  await until(page, 's.mode === "ON_FOOT"', 120_000);
  await untilPower(page, 'p && p.avatar && p.avatar.state === "climb"', 120_000);
  return untilPower(page, 'p && p.avatar && p.avatar.state !== "climb" && w', 180_000);
}
