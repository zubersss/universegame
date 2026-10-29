import { test, type Page } from '@playwright/test';
import { writeFileSync } from 'node:fs';
import { bootToTitle, collectErrors, snap } from '../helpers';

// Profiling route (fixed seed, every frame drawn): landed view, a short walk,
// low flight and a climb to the atmosphere edge, for each preset. Records the
// frame-interval distribution, draw calls, triangles, terrain chunks,
// colliders, an estimate of GPU allocations, JS heap and CPU-side timings.
// In this environment the renderer is SwiftShader (software); the numbers
// describe this machine only and say nothing about GPU performance.

test.use({ viewport: { width: 1280, height: 720 } });

const api = (page: Page, fn: string, ...args: unknown[]) =>
  page.evaluate(([f, a]) => (window as any).__meridian[f as string](...(a as unknown[])), [fn, args] as const);

async function sample(page: Page, label: string, frames: number, out: Record<string, unknown>[], preset: string): Promise<void> {
  // Every frame drawn while measuring (a few frames to settle first); between
  // samples only every 30th frame is drawn so the route itself is quicker.
  await api(page, 'setRenderEvery', 1);
  await api(page, 'resetFrames');
  await page.waitForFunction(() => (window as any).__meridian.game.frameIntervalCount >= 5, null, { timeout: 600_000, polling: 500 });
  await api(page, 'resetFrames');
  await page.waitForFunction((n) => (window as any).__meridian.game.frameIntervalCount >= n, frames, { timeout: 1_800_000, polling: 500 });
  const p = await api(page, 'perf', frames);
  const s = await snap(page);
  out.push({ label, mode: s.mode, clearance: s.clearance, simTime: s.simTime, ...p });
  await page.screenshot({ path: `evidence/perf-${preset}-${label}.png`, timeout: 300_000 });
  await api(page, 'setRenderEvery', 30);
  console.log(`${label}: ${JSON.stringify(p.frames)} calls=${p.draw.calls} tris=${p.draw.triangles} res=${p.draw.w}x${p.draw.h} chunks=${p.terrain?.rendered} gpu≈${p.gpu.totalMB.toFixed(0)}MB heap=${p.heapMB?.toFixed?.(0)}MB cpu(frame)=${p.timings.frame.toFixed(1)}ms render=${p.timings.render.toFixed(1)}ms`);
}

for (const preset of ['low', 'balanced', 'high']) {
  test(`profile route at ${preset}`, async ({ page }) => {
    test.setTimeout(3 * 60 * 60 * 1000);
    const errors = collectErrors(page);
    await bootToTitle(page, `?preset=${preset}&adaptive=0`);
    await page.click('#btn-new');
    await page.waitForFunction(() => (window as any).__meridian.snapshot().state === 'playing', null, { timeout: 900_000 });
    const out: Record<string, unknown>[] = [];
    await page.waitForTimeout(5000); // let terrain settle
    await sample(page, 'landed', 30, out, preset);
    await page.keyboard.press('KeyE');
    await page.waitForFunction(() => (window as any).__meridian.snapshot().mode === 'ON_FOOT', null, { timeout: 120_000 });
    await api(page, 'autopilot', { kind: 'walk', target: await api(page, 'dirNearShip', -30, 40), arrive: 2, sprint: true });
    await sample(page, 'walking', 30, out, preset);
    await api(page, 'autopilot', { kind: 'walk', target: 'ship', arrive: 2.5 });
    await page.waitForFunction(() => (window as any).__meridian.autopilotState().phase === 'arrived', null, { timeout: 1_800_000 });
    await api(page, 'autopilot', null);
    await page.keyboard.press('KeyE');
    await page.waitForFunction(() => (window as any).__meridian.snapshot().mode === 'LANDED', null, { timeout: 120_000 });
    await page.keyboard.press('Space');
    await api(page, 'autopilot', { kind: 'fly', dir: null, clearance: 120, throttle: 0.8 });
    await page.waitForFunction(() => (window as any).__meridian.snapshot().clearance > 90, null, { timeout: 1_800_000 });
    await sample(page, 'low-flight', 30, out, preset);
    await api(page, 'autopilot', { kind: 'fly', dir: null, clearance: 9000, throttle: 1, boost: true, pitchDeg: 40 });
    await page.waitForFunction(() => (window as any).__meridian.snapshot().altitude > 7000, null, { timeout: 3_000_000 });
    await sample(page, 'atmosphere-edge', 30, out, preset);
    const env = await page.evaluate(() => ({ ua: navigator.userAgent, dpr: devicePixelRatio, cores: navigator.hardwareConcurrency }));
    writeFileSync(`evidence/perf-${preset}.json`, JSON.stringify({ preset, env, samples: out, errors }, null, 1));
  });
}
