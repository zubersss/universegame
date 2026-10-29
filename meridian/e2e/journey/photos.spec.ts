import { expect, test, type Page } from '@playwright/test';
import { mkdirSync, writeFileSync } from 'node:fs';
import { join } from 'node:path';
import { Vector3 } from 'three';
import { bootToTitle, collectErrors, snap } from '../helpers';
import { BODIES, BODY_IDS, GENERATOR_VERSION, SAVE_SCHEMA_VERSION, WORLD_SEED, type BodyId } from '../../src/world/bodies';
import { computeSites } from '../../src/world/sites';
import { quatFromForwardUp } from '../../src/core/mathx';
import { GEAR_PAD_BOTTOM_Y } from '../../src/ship/ShipModel';

// LUMEN photo set (photography only, NOT travel acceptance: bodies are reached
// by importing a crafted save, never by flying there).
// Fixed, scripted camera poses per body, view and preset, so
// every visual change is judged against the same frames. Each body is reached
// by importing a backup parked on its landing site (Import Backup is a player
// action; no state hooks), then the test photo camera is placed in the
// landing-site frame (x right, y above the terrain, z toward the relay).
// Frames are drawn sparsely while terrain settles and every frame only
// while capturing. HUD is hidden so frames compare cleanly.
//
// PHOTO_SET=<name> picks the output folder (default "baseline");
// PHOTO_PRESETS / PHOTO_BODIES narrow a run (comma lists).

const SET = process.env.PHOTO_SET ?? 'baseline';
const OUT = join('evidence/studio/lumen', SET);
const PRESETS = (process.env.PHOTO_PRESETS ?? 'low,balanced,high').split(',');
const ONLY = process.env.PHOTO_BODIES?.split(',');
const PHOTO_BODIES = BODY_IDS.filter((b) => !ONLY || ONLY.includes(b));

type Pose = { eye: [number, number, number]; target: [number, number, number] };

/** Views in landing-site meters; orbit scales with the body radius. */
function views(id: BodyId): Record<string, Pose> {
  const R = BODIES[id].radius;
  return {
    ground: { eye: [-28, 1.8, -24], target: [30, 3, 160] },
    'low-flight': { eye: [-260, 140, -380], target: [60, 0, 500] },
    'high-flight': { eye: [-2500, 3200, -5200], target: [0, 0, 3000] },
    orbit: { eye: [-0.9 * R, 1.6 * R, -1.3 * R], target: [0, 0, 0] },
  };
}

/** Views also taken at 640×360 (Balanced). */
const SMALL_VIEWS = ['ground', 'low-flight', 'orbit'];

function landedSave(id: BodyId): string {
  const def = BODIES[id];
  const sites = computeSites(def);
  const n = new Vector3(...sites.landing.dir);
  const pos = n.clone().multiplyScalar(def.radius + sites.landing.height - GEAR_PAD_BOTTOM_Y);
  const relay = new Vector3(...sites.relay.dir);
  const fwd = relay.sub(n.clone().multiplyScalar(relay.dot(n))).normalize();
  const q = quatFromForwardUp(fwd, n);
  return JSON.stringify({
    schema: SAVE_SCHEMA_VERSION, generator: GENERATOR_VERSION, seed: WORLD_SEED,
    savedAt: '2026-10-29T00:00:00.000Z', playTime: 60, mode: 'LANDED', body: id,
    ship: { sys: [def.center[0] + pos.x, def.center[1] + pos.y, def.center[2] + pos.z], quat: [q.x, q.y, q.z, q.w], vel: [0, 0, 0], gear: 1, throttle: 0 },
    player: null, cruise: null, lastSafeLanding: null, navTarget: null, settings: {},
    expedition: { inventory: { ilex: 0, vesper: 0, cairn: 0 }, collected: [], relays: [], species: [], scanned: [], transmitted: false },
  });
}

const api = (page: Page, fn: string, ...args: unknown[]) =>
  page.evaluate(([f, a]) => (window as any).__meridian[f as string](...(a as unknown[])), [fn, args] as const);

/** Terrain, props and proxies idle for a few consecutive checks (sparse drawing meanwhile). */
async function settle(page: Page): Promise<void> {
  await api(page, 'setRenderEvery', 20);
  let quiet = 0;
  for (let i = 0; i < 600 && quiet < 4; i++) {
    await page.waitForTimeout(1000);
    const s = await snap(page);
    const busy = s.chunks.queued + s.chunks.inFlight + (s.props?.pending ?? 0);
    quiet = busy === 0 && s.state === 'playing' ? quiet + 1 : 0;
  }
}

async function capture(page: Page, file: string, meta: Record<string, unknown>[], label: Record<string, unknown>): Promise<void> {
  await settle(page);
  await api(page, 'setRenderEvery', 1);
  await api(page, 'resetFrames');
  await page.waitForFunction(() => (window as any).__meridian.game.frameIntervalCount >= 4, null, { timeout: 600_000, polling: 250 });
  const p = (await api(page, 'perf', 3)) as Record<string, any>;
  const programs = await page.evaluate(() => (window as any).__meridian.game.render.renderer.info.programs?.length ?? null);
  await page.screenshot({ path: join(OUT, file), timeout: 300_000 });
  meta.push({ ...label, file, calls: p.draw.calls, triangles: p.draw.triangles, gpuMB: Math.round(p.gpu.totalMB), programs, heapMB: p.heapMB, chunks: p.terrain?.rendered });
  await api(page, 'setRenderEvery', 20);
}

test.use({ viewport: { width: 1280, height: 720 } });

for (const preset of PRESETS) {
  test(`photo set at ${preset}`, async ({ page }) => {
    test.setTimeout(4 * 60 * 60 * 1000);
    mkdirSync(OUT, { recursive: true });
    mkdirSync('scratch', { recursive: true });
    const errors = collectErrors(page);
    const meta: Record<string, unknown>[] = [];
    await bootToTitle(page, `?preset=${preset}&adaptive=0`);
    await page.addStyleTag({ content: '#hud{visibility:hidden !important}' });
    for (const [i, id] of PHOTO_BODIES.entries()) {
      const file = join('scratch', `photo-save-${id}.json`);
      writeFileSync(file, landedSave(id));
      if (i > 0) {
        await page.keyboard.press('Escape');
        await expect(page.locator('#btn-resume')).toBeVisible();
      }
      await page.setInputFiles('#file-import', file);
      await page.waitForFunction((b) => {
        const s = (window as any).__meridian.snapshot();
        return s.mode === 'LANDED' && s.terrain && s.state === 'playing' && s.body === b;
      }, id, { timeout: 1_800_000, polling: 500 });
      if (i > 0 && (await page.locator('#btn-resume').isVisible())) await page.click('#btn-resume');
      for (const [view, pose] of Object.entries(views(id))) {
        await api(page, 'photo', pose.eye, pose.target);
        await capture(page, `${id}-${view}-${preset}.png`, meta, { body: id, view, preset, size: '1280x720' });
        if (preset === 'balanced' && SMALL_VIEWS.includes(view)) {
          await page.setViewportSize({ width: 640, height: 360 });
          await capture(page, `${id}-${view}-${preset}-640.png`, meta, { body: id, view, preset, size: '640x360' });
          await page.setViewportSize({ width: 1280, height: 720 });
        }
      }
      await api(page, 'photo', null);
    }
    writeFileSync(join(OUT, `perf-${preset}.json`), JSON.stringify({ preset, photos: meta, errors }, null, 1));
    expect(errors).toEqual([]);
  });
}
