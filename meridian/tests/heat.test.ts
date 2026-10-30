import { readFileSync } from 'node:fs';
import { describe, expect, it } from 'vitest';
import { Vector3 } from 'three';
import { HeatTimer, heatWarning, heatZone } from '../src/game/Heat';
import { FLIGHT, SIM_DT, SUN_HEAT } from '../src/game/config';
import { CruiseController, safetyRadius } from '../src/ship/Cruise';
import { starOf } from '../src/render/Lighting';
import { quatFromForwardUp } from '../src/core/mathx';
import { BODIES, SYSTEM_BODY_IDS } from '../src/world/bodies';
import { bodyGravity } from '../src/world/environment';

// The Sun's heat hazard (LEAD-M2 step 5), in Node: zones, the danger
// countdown, the HUD lines, and where the zones sit against the Sun's gravity
// and its cruise envelope. Game steps the timer while flying and acts on the
// recall after the fixed steps.

const sun = BODIES.sun;
const R = sun.radius;

describe('heat zones', () => {
  it('caution inside 3R, danger inside 2R, recall inside 1.75R', () => {
    expect(heatZone(3.01 * R, R)).toBe('none');
    expect(heatZone(2.99 * R, R)).toBe('caution');
    expect(heatZone(2.01 * R, R)).toBe('caution');
    expect(heatZone(1.99 * R, R)).toBe('danger');
    expect(heatZone(1.76 * R, R)).toBe('danger');
    expect(heatZone(1.74 * R, R)).toBe('recall');
    expect(heatZone(0, R)).toBe('recall');
  });

  it('only a star heats: the Sun in Sol, nothing in the Quiet System', () => {
    expect(starOf(BODIES.earth)).toBe(sun);
    expect(starOf(BODIES.jupiter)).toBe(sun);
    for (const id of SYSTEM_BODY_IDS.quiet) expect(starOf(BODIES[id])).toBeNull();
  });

  it('the hard radius sits where the ship can still outclimb the Sun, and cruise never enters a zone', () => {
    const g = new Vector3();
    bodyGravity(sun, SUN_HEAT.hardRadii * R, 0, 0, g);
    expect(g.length()).toBeLessThan(FLIGHT.accelSpace);
    // Inside 1.65R the Sun outpulls the ship: the recall must come first.
    bodyGravity(sun, 1.65 * R, 0, 0, g);
    expect(g.length()).toBeGreaterThan(FLIGHT.accelSpace);
    expect(safetyRadius(sun)).toBeGreaterThan(SUN_HEAT.cautionRadii * R);
  });

  it('the recall point is cool and cruise can engage there facing away', () => {
    const out = new Vector3(0.3, 0.2, -0.9).normalize();
    const c = new Vector3(...sun.center);
    const p = c.clone().addScaledVector(out, safetyRadius(sun) + SUN_HEAT.recallStandoff);
    expect(heatZone(p.distanceTo(c), R)).toBe('none');
    const up = new Vector3(0, 1, 0);
    const chk = CruiseController.canEngage(p, quatFromForwardUp(out, up), 0, SYSTEM_BODY_IDS.sol);
    expect(chk).toEqual({ ok: true, reason: null });
  });
});

describe('heat timer', () => {
  it('counts down only in the danger zone and resets outside it', () => {
    const t = new HeatTimer();
    for (let i = 0; i < 600; i++) t.step(SIM_DT, 'caution');
    expect(t.remaining).toBe(SUN_HEAT.recallSeconds);
    expect(t.recall).toBe(false);
    for (let i = 0; i < 600; i++) t.step(SIM_DT, 'danger');
    expect(t.remaining).toBeCloseTo(SUN_HEAT.recallSeconds - 10, 6);
    expect(t.recall).toBe(false);
    t.step(SIM_DT, 'caution');
    expect(t.remaining).toBe(SUN_HEAT.recallSeconds);
    t.step(SIM_DT, 'none');
    expect(t.zone).toBe('none');
    expect(t.recall).toBe(false);
  });

  it('recalls when the countdown runs out (15 s in danger), and stays due until reset', () => {
    const t = new HeatTimer();
    let steps = 0;
    while (!t.step(SIM_DT, 'danger') && steps < 10000) steps++;
    expect((steps + 1) * SIM_DT).toBeCloseTo(SUN_HEAT.recallSeconds, 1);
    expect(t.remaining).toBe(0);
    // Leaving the zone after the countdown ran out does not cancel the recall.
    expect(t.step(SIM_DT, 'none')).toBe(true);
    t.reset();
    expect(t.recall).toBe(false);
    expect(t.remaining).toBe(SUN_HEAT.recallSeconds);
    expect(t.zone).toBe('none');
  });

  it('recalls at once inside the hard radius', () => {
    const t = new HeatTimer();
    expect(t.step(SIM_DT, 'recall')).toBe(true);
    expect(t.remaining).toBe(SUN_HEAT.recallSeconds);
  });

  it('no timer state survives a load, recover or new expedition: the countdown restarts at 15 s', () => {
    // Reset part-way through the countdown, as Game does on a placement: the next danger step counts from 15 s.
    const t = new HeatTimer();
    while (t.remaining > 3) t.step(SIM_DT, 'danger');
    t.reset();
    t.step(SIM_DT, 'danger');
    expect(t.remaining).toBeCloseTo(SUN_HEAT.recallSeconds - SIM_DT, 9);
    // Game resets the timer in restore() (a load into the same game) and in
    // placeShipLanded(), which recover() and newExpedition() go through.
    const src = readFileSync(new URL('../src/game/Game.ts', import.meta.url), 'utf8');
    const body = (sig: string) => src.slice(src.indexOf(sig), src.indexOf('\n  }\n', src.indexOf(sig)));
    for (const sig of ['  restore(data: SaveData): void {', '  placeShipLanded(bodyId: BodyId, posPlanet: Vector3, quat: Quaternion): void {']) {
      expect(body(sig)).toMatch(/this\.heat\.reset\(\);\s*this\.heatStar = null;/);
    }
    expect(body('  recover(): void {')).toMatch(/this\.placeShipLanded\(/);
    expect(body('  newExpedition(): void {')).toMatch(/this\.placeShipLanded\(/);
  });
});

describe('heat warnings', () => {
  it('caution, then a danger countdown, then the recall line; nothing outside', () => {
    const t = new HeatTimer();
    t.step(SIM_DT, 'none');
    expect(heatWarning(t, sun.name)).toBeNull();
    t.step(SIM_DT, 'caution');
    expect(heatWarning(t, sun.name)).toEqual({ text: 'Solar heat rising: turn away from the Sun', danger: false });
    for (let i = 0; i < 90; i++) t.step(SIM_DT, 'danger');
    expect(heatWarning(t, sun.name)).toEqual({ text: 'Heat shield failing: emergency recall in 14 s', danger: true });
    t.step(SIM_DT, 'recall');
    expect(heatWarning(t, sun.name)?.danger).toBe(true);
  });
});
