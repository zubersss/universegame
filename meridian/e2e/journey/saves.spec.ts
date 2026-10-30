import { expect, test, type Page } from '@playwright/test';
import { readFileSync, writeFileSync } from 'node:fs';
import { bootToTitle, collectErrors, snap } from '../helpers';

// Save robustness through the real UI: corrupt latest record, storage denied,
// backup export and import (valid and invalid files), and a save from an
// earlier version kept as read-only history.

test.use({ viewport: { width: 640, height: 360 } });

/** A schema-1 record as the published build wrote it (shared with tests/save.test.ts). */
const SCHEMA1_FILE = 'tests/fixtures/save-schema1.json';

const api = (page: Page, fn: string, ...args: unknown[]) =>
  page.evaluate(([f, a]) => (window as any).__meridian[f as string](...(a as unknown[])), [fn, args] as const);

async function until(page: Page, src: string, timeoutMs = 600_000): Promise<Record<string, any>> {
  await page.waitForFunction((s) => new Function('s', `return (${s});`)((window as any).__meridian.snapshot()), src, { timeout: timeoutMs, polling: 300 });
  return snap(page);
}

async function idbGet(page: Page, key: string): Promise<unknown> {
  return page.evaluate(async (k) => {
    const db: IDBDatabase = await new Promise((res, rej) => {
      const r = indexedDB.open('meridian', 1);
      r.onsuccess = () => res(r.result);
      r.onerror = () => rej(r.error);
    });
    const v = await new Promise((res, rej) => {
      const r = db.transaction('kv', 'readonly').objectStore('kv').get(k);
      r.onsuccess = () => res(r.result);
      r.onerror = () => rej(r.error);
    });
    db.close();
    return v;
  }, key);
}

async function idbPut(page: Page, key: string, value: unknown): Promise<void> {
  await page.evaluate(async ([k, v]) => {
    const db: IDBDatabase = await new Promise((res, rej) => {
      const r = indexedDB.open('meridian', 1);
      r.onsuccess = () => res(r.result);
      r.onerror = () => rej(r.error);
    });
    await new Promise((res, rej) => {
      const tx = db.transaction('kv', 'readwrite');
      tx.objectStore('kv').put(v, k as string);
      tx.oncomplete = res;
      tx.onerror = rej;
    });
    db.close();
  }, [key, value] as const);
}

async function pauseAndSave(page: Page): Promise<void> {
  await page.keyboard.press('Escape');
  await until(page, 's.state === "paused"', 30_000);
  const before = (await api(page, 'saveState')).latest.savedAt;
  await page.click('#btn-save');
  await page.waitForFunction((b) => {
    const st = (window as any).__meridian.saveState();
    return st.latest.valid && st.latest.savedAt !== b;
  }, before, { timeout: 30_000 });
}

test('a corrupt latest save offers the previous save and is kept aside', async ({ page }) => {
  test.setTimeout(30 * 60 * 1000);
  const errors = collectErrors(page);
  await bootToTitle(page, '?preset=low');
  await api(page, 'setRenderEvery', 30);
  await page.click('#btn-new');
  await until(page, 's.state === "playing"');
  await pauseAndSave(page);
  await page.click('#btn-resume');
  await until(page, 's.state === "playing"', 30_000);
  await pauseAndSave(page);
  expect(await idbGet(page, 'save-prev')).toBeTruthy();
  // Damage the latest record.
  await idbPut(page, 'save', { schema: 2, ship: 'garbage' });
  await page.reload();
  await page.waitForFunction(() => (window as any).__meridianBooted === true, null, { timeout: 180_000 });
  await expect(page.locator('#btn-continue')).toBeHidden();
  await expect(page.locator('#btn-continue-prev')).toBeVisible();
  await expect(page.locator('#title-save-note')).toContainText('could not be loaded');
  await api(page, 'setRenderEvery', 30);
  await page.click('#btn-continue-prev');
  await until(page, 's.state === "playing"');
  await pauseAndSave(page);
  expect(await idbGet(page, 'save-corrupt')).toEqual({ schema: 2, ship: 'garbage' });
  const latest = (await idbGet(page, 'save')) as Record<string, unknown>;
  expect(latest.schema).toBe(2);
  expect(latest.mode).toBe('LANDED');
  expect(errors).toEqual([]);
});

test('denied storage keeps the game playable; export and import still work', async ({ page }, info) => {
  test.setTimeout(30 * 60 * 1000);
  await page.addInitScript(() => {
    Object.defineProperty(window, 'indexedDB', {
      configurable: true,
      get() {
        throw new DOMException('The user denied permission to access the database.', 'SecurityError');
      },
    });
  });
  const errors = collectErrors(page);
  await bootToTitle(page, '?preset=low');
  await expect(page.locator('#title-save-note')).toContainText('storage is unavailable');
  await api(page, 'setRenderEvery', 30);
  await page.click('#btn-new');
  await until(page, 's.state === "playing"');
  await page.keyboard.press('Space'); // still playable: take off
  await until(page, 's.mode === "PILOTING" && s.clearance > 10', 120_000);
  await page.keyboard.press('Escape');
  await until(page, 's.state === "paused"', 30_000);
  await page.click('#btn-save');
  await expect(page.locator('#pause-status')).toContainText('unavailable');
  const dl = page.waitForEvent('download');
  await page.click('#btn-export');
  const file = info.outputPath('backup.json');
  await (await dl).saveAs(file);
  const backup = JSON.parse(readFileSync(file, 'utf8'));
  expect(backup.schema).toBe(2);
  expect(backup.mode).toBe('PILOTING');
  // Re-import the backup (restores the flight state).
  await page.setInputFiles('#file-import', file);
  const s = await until(page, 's.state === "playing" && s.mode === "PILOTING"', 300_000);
  expect(s.counters.restores).toBeGreaterThanOrEqual(1);
  expect(errors).toEqual([]);
});

test('a backup carries progress into a fresh profile; invalid files are rejected', async ({ page, browser }, info) => {
  test.setTimeout(45 * 60 * 1000);
  await bootToTitle(page, '?preset=low');
  await api(page, 'setRenderEvery', 30);
  await page.click('#btn-new');
  await until(page, 's.state === "playing"');
  // Collect one Ilex sample through normal play.
  await page.keyboard.press('KeyE');
  await until(page, 's.mode === "ON_FOOT" && s.player && s.player.grounded', 120_000);
  const targets = (await api(page, 'missionTargets')) as { id: string; kind: string; dir: number[] }[];
  const sample = targets.find((t) => t.kind === 'sample')!;
  await api(page, 'autopilot', { kind: 'walk', target: sample.dir, arrive: 1.4, sprint: true });
  await page.waitForFunction(() => (window as any).__meridian.autopilotState().phase === 'arrived', null, { timeout: 600_000 });
  await api(page, 'autopilot', null);
  await page.keyboard.press('KeyE');
  await until(page, `s.expedition.collected.includes("${sample.id}")`, 60_000);
  await page.keyboard.press('Escape');
  await until(page, 's.state === "paused"', 30_000);
  const dl = page.waitForEvent('download');
  await page.click('#btn-export');
  const file = info.outputPath('progress.json');
  await (await dl).saveAs(file);

  // Fresh profile: empty storage.
  const ctx = await browser.newContext({ viewport: { width: 640, height: 360 }, baseURL: info.project.use.baseURL });
  const fresh = await ctx.newPage();
  const errors = collectErrors(fresh);
  await bootToTitle(fresh, '?preset=low');
  await expect(fresh.locator('#btn-continue')).toBeHidden();
  // Invalid file first: rejected with a message, nothing restored.
  const bad = info.outputPath('bad.json');
  writeFileSync(bad, JSON.stringify({ schema: 2, hello: 'world' }));
  await fresh.setInputFiles('#file-import', bad);
  await expect(fresh.locator('#title-save-note')).toContainText('Import failed');
  expect((await snap(fresh)).state).toBe('title');
  // Valid backup.
  await api(fresh, 'setRenderEvery', 30);
  await fresh.setInputFiles('#file-import', file);
  const s = await until(fresh, 's.state === "playing"', 600_000);
  expect(s.mode).toBe('ON_FOOT');
  expect(s.expedition.collected).toContain(sample.id);
  expect(s.expedition.inventory.ilex).toBe(1);
  // The import was persisted in the fresh profile.
  await fresh.waitForFunction(() => (window as any).__meridian.saveState().latest.valid, null, { timeout: 30_000 });
  expect(errors).toEqual([]);
  await ctx.close();
});

test('an earlier-version save is kept as read-only history', async ({ page }) => {
  test.setTimeout(20 * 60 * 1000);
  const errors = collectErrors(page);
  const old = JSON.parse(readFileSync(SCHEMA1_FILE, 'utf8'));
  await bootToTitle(page, '?preset=low');
  // A player of the published build: their schema-1 record is the latest save.
  await idbPut(page, 'save', old);
  await page.reload();
  await page.waitForFunction(() => (window as any).__meridianBooted === true, null, { timeout: 180_000 });
  await expect(page.locator('#btn-continue')).toBeHidden();
  await expect(page.locator('#btn-continue-prev')).toBeHidden();
  const history = page.locator('#title-legacy');
  await expect(history).toBeVisible();
  await expect(history).toContainText('read-only history');
  await expect(history).toContainText('Vesper');
  expect(await idbGet(page, 'save-legacy')).toEqual(old);
  // The same record as a backup file is refused with a reason, not restored.
  await page.setInputFiles('#file-import', SCHEMA1_FILE);
  await expect(page.locator('#title-save-note')).toContainText('earlier version');
  expect((await snap(page)).state).toBe('title');
  // A new expedition plays and saves beside the history.
  await api(page, 'setRenderEvery', 30);
  await page.click('#btn-new');
  const s = await until(page, 's.state === "playing"');
  expect(s.discoveries).toEqual(['ilex']);
  await pauseAndSave(page);
  await page.reload();
  await page.waitForFunction(() => (window as any).__meridianBooted === true, null, { timeout: 180_000 });
  await expect(page.locator('#btn-continue')).toBeVisible();
  await expect(history).toContainText('read-only history');
  const st = await api(page, 'saveState');
  expect(st.latest.valid).toBe(true);
  expect(st.latest.system).toBe('quiet');
  expect(st.legacy.schema).toBe(1);
  expect(await idbGet(page, 'save-legacy')).toEqual(old);
  expect(errors).toEqual([]);
});

test('settings persist across a reload', async ({ page }) => {
  test.setTimeout(10 * 60 * 1000);
  const errors = collectErrors(page);
  await bootToTitle(page, '?preset=low');
  await page.click('#btn-settings-title');
  await expect(page.locator('#screen-settings')).toBeVisible();
  await page.locator('#set-invert').check();
  await page.locator('#set-reduced').check();
  await page.locator('#set-sens').fill('1.6');
  await page.locator('#set-volume').fill('0.35');
  await page.click('#btn-settings-back');
  // Settings are written asynchronously; wait for the record to land.
  await page.waitForFunction(async () => {
    const db: IDBDatabase = await new Promise((res, rej) => {
      const r = indexedDB.open('meridian', 1);
      r.onsuccess = () => res(r.result);
      r.onerror = () => rej(r.error);
    });
    const v: any = await new Promise((res) => {
      const r = db.transaction('kv', 'readonly').objectStore('kv').get('settings');
      r.onsuccess = () => res(r.result);
    });
    db.close();
    return v && v.invertY === true && Math.abs(v.sensitivity - 1.6) < 1e-6;
  }, null, { timeout: 30_000 });
  await page.reload();
  await page.waitForFunction(() => (window as any).__meridianBooted === true, null, { timeout: 180_000 });
  await page.click('#btn-settings-title');
  await expect(page.locator('#set-invert')).toBeChecked();
  await expect(page.locator('#set-reduced')).toBeChecked();
  await expect(page.locator('#set-sens')).toHaveValue('1.6');
  await expect(page.locator('#set-volume')).toHaveValue('0.35');
  expect((await snap(page)).state).toBe('title');
  const live = await page.evaluate(() => (window as any).__meridian.game.settings);
  expect(live.invertY).toBe(true);
  expect(live.sensitivity).toBeCloseTo(1.6, 6);
  expect(errors).toEqual([]);
});
