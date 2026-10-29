import { expect, test, type Page } from '@playwright/test';
import { bootToTitle, collectErrors, snap, stubPointerLock } from '../helpers';

// Phase 4 gate: ten consecutive land → exit → walk/jump → re-enter → take off
// cycles across several surveyed sites, plus a steep-site landing rejection.
// All motion is produced through player inputs (keyboard events and the
// test autopilot's injected keys/mouse), never by assigning state.

test.use({ viewport: { width: 640, height: 360 } });

const api = (page: Page, fn: string, ...args: unknown[]) =>
  page.evaluate(([f, a]) => (window as any).__meridian[f as string](...(a as unknown[])), [fn, args] as const);

async function until(page: Page, src: string, timeoutMs = 600_000): Promise<Record<string, any>> {
  await page.waitForFunction((s) => new Function('s', `return (${s});`)((window as any).__meridian.snapshot()), src, {
    timeout: timeoutMs,
    polling: 300,
  });
  return snap(page);
}

async function apPhase(page: Page, phases: string[], timeoutMs = 600_000): Promise<string> {
  await page.waitForFunction((ps) => ps.includes((window as any).__meridian.autopilotState().phase), phases, {
    timeout: timeoutMs,
    polling: 300,
  });
  return (await api(page, 'autopilotState')).phase;
}

test('ten land–exit–walk–board–takeoff cycles and steep-site rejection', async ({ page }) => {
  test.setTimeout(150 * 60 * 1000);
  const errors = collectErrors(page);
  await stubPointerLock(page);
  await bootToTitle(page, '?preset=low');
  await api(page, 'setRenderEvery', 16);
  await page.click('#btn-new');
  let s = await until(page, 's.state === "playing"');
  expect(s.mode).toBe('LANDED');
  const log: string[] = [];
  let worstGap = 0;
  let worstDrift = 0;
  let rejectionsSeen = 0;

  // Steep-site rejection first: find a steep spot, try to land, expect a hold with a reason.
  await page.keyboard.press('Space');
  await until(page, 's.mode === "PILOTING" && s.clearance > 15', 120_000);
  let steep: number[] | null = null;
  for (const [a, b] of [[300, 1500], [1500, 4000], [4000, 9000]]) {
    const sv = await api(page, 'surveySites', 1, a, b);
    if (sv.steep.length) {
      steep = sv.steep[0];
      break;
    }
  }
  expect(steep).not.toBeNull();
  await api(page, 'autopilot', { kind: 'land', dir: steep, approachClearance: 90 });
  await apPhase(page, ['rejected', 'landed'], 1_800_000);
  s = await snap(page);
  log.push(`steep: mode=${s.mode} assist=${JSON.stringify(s.assist)} probeSlope=${s.probe.slope.toFixed(1)}`);
  expect(s.mode).toBe('PILOTING');
  expect(s.assist.reason ?? '').toMatch(/steep|obstructed|Uneven/i);
  rejectionsSeen = s.counters.rejectedLandings;
  expect(rejectionsSeen).toBeGreaterThanOrEqual(1);
  // Disengage and climb away.
  await api(page, 'autopilot', null);
  await page.keyboard.press('KeyL');
  await api(page, 'autopilot', { kind: 'fly', dir: null, clearance: 120, throttle: 0 });
  await until(page, 's.clearance > 80 && !s.assist.active', 300_000);
  console.log(log[0]);

  for (let cycle = 0; cycle < 10; cycle++) {
    // Fly to a new flat site and land with the assist.
    const sv = await api(page, 'surveySites', 1, 260 + cycle * 40, 700 + cycle * 60);
    expect(sv.flat.length).toBeGreaterThan(0);
    await api(page, 'autopilot', { kind: 'land', dir: sv.flat[0], approachClearance: 70 });
    const ph = await apPhase(page, ['landed', 'rejected'], 1_800_000);
    if (ph === 'rejected') {
      // Unexpected obstruction on a surveyed flat site: try the next candidate.
      const sv2 = await api(page, 'surveySites', 2, 300, 900);
      await api(page, 'autopilot', null);
      await page.keyboard.press('KeyL');
      await api(page, 'autopilot', { kind: 'land', dir: sv2.flat[1], approachClearance: 70 });
      await apPhase(page, ['landed'], 1_800_000);
    }
    s = await until(page, 's.mode === "LANDED"', 60_000);
    expect(s.probe.reason).toBeNull();
    expect(s.probe.slope).toBeLessThanOrEqual(12);
    await api(page, 'autopilot', null);

    // Exit (real key event), walk out ~25 m with a jump, stand, measure, walk back.
    await page.keyboard.press('KeyE');
    s = await until(page, 's.mode === "ON_FOOT" && s.player && s.player.grounded', 60_000);
    // Targets stay on the ladder side so the walk does not route under the hull.
    const out = await api(page, 'dirNearShip', -18 - (cycle % 3) * 4, cycle % 2 ? 10 + cycle : -6 - cycle);
    await api(page, 'autopilot', { kind: 'walk', target: out, arrive: 2, jumpAt: 12, sprint: cycle % 3 === 0 });
    await apPhase(page, ['arrived'], 600_000);
    await api(page, 'autopilot', null);
    // Standing drift is measured from rest (after the walk deceleration has
    // finished) over three seconds of simulated time with no input.
    s = await until(page, 's.player && s.player.grounded && s.player.speed < 0.01 && Math.abs(s.player.vVert) < 0.01', 60_000);
    const p0 = s.player.system as number[];
    const t0 = s.simTime as number;
    s = await until(page, `s.simTime >= ${t0 + 3}`, 120_000);
    const p1 = s.player.system as number[];
    const drift = Math.hypot(p1[0] - p0[0], p1[1] - p0[1], p1[2] - p0[2]);
    worstDrift = Math.max(worstDrift, drift);
    const gd = await api(page, 'groundDisagreement');
    expect(gd).not.toBeNull();
    worstGap = Math.max(worstGap, Math.abs(gd.mesh - gd.physics), Math.abs(gd.feetToMesh));
    expect(s.counters.jumps).toBeGreaterThanOrEqual(cycle + 1);
    await api(page, 'autopilot', { kind: 'walk', target: 'ship', arrive: 2.5 });
    await apPhase(page, ['arrived'], 600_000);
    await api(page, 'autopilot', null);
    await page.keyboard.press('KeyE');
    s = await until(page, 's.mode === "LANDED"', 60_000);

    // Take off (real key event).
    await page.keyboard.press('Space');
    s = await until(page, 's.mode === "PILOTING" && s.clearance > 15', 120_000);
    console.log(`cycle ${cycle + 1} done at t=${s.simTime.toFixed(0)}`);
    log.push(`cycle ${cycle + 1}: t=${s.simTime.toFixed(0)} landings=${s.counters.landings} exits=${s.counters.exits} boardings=${s.counters.boardings} takeoffs=${s.counters.takeoffs} drift=${(drift * 1000).toFixed(1)}mm meshGap=${(gd.feetToMesh * 100).toFixed(1)}cm meshVsPhysics=${(Math.abs(gd.mesh - gd.physics) * 1000).toFixed(2)}mm rebases=${s.rebaseCount}`);
  }
  s = await snap(page);
  console.log(log.join('\n'));
  console.log(`worst contact gap ${(worstGap * 100).toFixed(1)} cm, worst standing drift ${(worstDrift * 1000).toFixed(1)} mm`);
  expect(s.counters.landings).toBeGreaterThanOrEqual(10);
  expect(s.counters.exits).toBeGreaterThanOrEqual(10);
  expect(s.counters.boardings).toBeGreaterThanOrEqual(10);
  expect(s.counters.takeoffs).toBeGreaterThanOrEqual(11);
  expect(s.counters.recoveries).toBe(0); // no recovery needed for routine traversal
  expect(worstGap).toBeLessThan(0.15);
  expect(worstDrift).toBeLessThan(0.05);
  await api(page, 'setRenderEvery', 1);
  await page.waitForTimeout(4000);
  await page.screenshot({ path: 'evidence/phase4-after-cycles.png', timeout: 180_000 });
  expect(errors).toEqual([]);
});
