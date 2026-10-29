import { describe, expect, it } from 'vitest';
import { Quaternion, Vector3 } from 'three';
import { CruiseController, freeDistance, insideEnvelope, safetyRadius, type CruiseInput } from '../src/ship/Cruise';
import { BODIES, BODY_IDS } from '../src/world/bodies';
import { CRUISE, SIM_DT } from '../src/game/config';
import { FixedStepper } from '../src/core/loop';
import { quatFromForwardUp } from '../src/core/mathx';

const IDLE: CruiseInput = { pitch: 0, yaw: 0, roll: 0, throttle: 1, brake: false, toggleOff: false };

function center(id: keyof typeof BODIES): Vector3 {
  const c = BODIES[id].center;
  return new Vector3(c[0], c[1], c[2]);
}

/** Minimum distance from `p` to any safety envelope surface (negative inside). */
function envelopeClearance(p: Vector3): number {
  let m = Infinity;
  for (const id of BODY_IDS) m = Math.min(m, p.distanceTo(center(id)) - safetyRadius(BODIES[id]));
  return m;
}

function facing(from: Vector3, to: Vector3): Quaternion {
  const f = to.clone().sub(from).normalize();
  const up = Math.abs(f.y) > 0.9 ? new Vector3(1, 0, 0) : new Vector3(0, 1, 0);
  return quatFromForwardUp(f, up);
}

describe('cruise', () => {
  it('refuses to engage inside an envelope or facing a nearby envelope', () => {
    const ilex = center('ilex');
    const near = ilex.clone().add(new Vector3(0, BODIES.ilex.radius + 9000, 0));
    expect(insideEnvelope(near)).toBe('ilex');
    const r1 = CruiseController.canEngage(near, new Quaternion(), 300);
    expect(r1.ok).toBe(false);
    expect(r1.reason).toMatch(/Too close to Ilex/);
    // Just outside the envelope but pointed straight at the planet.
    const out = ilex.clone().add(new Vector3(0, safetyRadius(BODIES.ilex) + 2000, 0));
    const r2 = CruiseController.canEngage(out, facing(out, ilex), 300);
    expect(r2.ok).toBe(false);
    // Pointed away: allowed.
    const r3 = CruiseController.canEngage(out, facing(out, out.clone().multiplyScalar(2)), 300);
    expect(r3.ok).toBe(true);
  });

  it('approaches a body at cruise speed and hands back before its envelope', () => {
    const vesper = center('vesper');
    const start = vesper.clone().add(new Vector3(400000, 30000, -20000));
    const c = new CruiseController();
    c.begin(start, facing(start, vesper), new Vector3());
    let maxSpeed = 0;
    let maxDecel = 0;
    let minClear = Infinity;
    let exit = null;
    let t = 0;
    for (let i = 0; i < 60 * 300 && !exit; i++) {
      const v0 = c.speed;
      exit = c.step(SIM_DT, IDLE).exit;
      t += SIM_DT;
      maxSpeed = Math.max(maxSpeed, c.speed);
      maxDecel = Math.max(maxDecel, (v0 - c.speed) / SIM_DT);
      minClear = Math.min(minClear, envelopeClearance(c.pos));
    }
    expect(exit).toBe('approach');
    expect(maxSpeed).toBeGreaterThan(CRUISE.maxSpeed * 0.99);
    expect(maxDecel).toBeLessThanOrEqual(CRUISE.accel + 1e-6);
    expect(c.speed).toBeLessThanOrEqual(CRUISE.exitSpeed + 1e-6);
    expect(minClear).toBeGreaterThan(0);
    expect(envelopeClearance(c.pos)).toBeLessThan(6000);
    expect(c.safetyStops).toBe(0);
    console.log(`approach: ${t.toFixed(1)} s, exit ${(envelopeClearance(c.pos) / 1000).toFixed(2)} km outside the envelope at ${c.speed.toFixed(0)} m/s`);
  });

  it('brake cancels cruise with bounded deceleration', () => {
    const p = new Vector3(300000, 400000, 0);
    const c = new CruiseController();
    c.begin(p, facing(p, p.clone().add(new Vector3(1, 0, 0))), new Vector3());
    for (let i = 0; i < 60 * 5; i++) c.step(SIM_DT, IDLE);
    expect(c.speed).toBeGreaterThan(14000);
    let exit = null;
    let steps = 0;
    while (!exit && steps < 60 * 10) {
      const v0 = c.speed;
      exit = c.step(SIM_DT, { ...IDLE, brake: true }).exit;
      expect(v0 - c.speed).toBeLessThanOrEqual(CRUISE.accel * SIM_DT + 1e-6);
      steps++;
    }
    expect(exit).toBe('brake');
    expect(c.speed).toBeLessThanOrEqual(CRUISE.exitSpeed + 1e-6);
    // 15 km/s to 0.9 km/s at 5 km/s^2 is about 2.8 s.
    expect(steps * SIM_DT).toBeLessThan(3.2);
  });

  it('limits turning to the cruise turn rate', () => {
    const p = new Vector3(300000, 400000, 0);
    const c = new CruiseController();
    c.begin(p, facing(p, p.clone().add(new Vector3(1, 0, 0))), new Vector3());
    const f0 = new Vector3(0, 0, -1).applyQuaternion(c.quat);
    for (let i = 0; i < 60; i++) c.step(SIM_DT, { ...IDLE, pitch: 1, yaw: 1 });
    const f1 = new Vector3(0, 0, -1).applyQuaternion(c.quat);
    const angle = f0.angleTo(f1);
    expect(angle).toBeLessThanOrEqual(CRUISE.turnRate * 1.0 + 1e-6);
    expect(angle).toBeGreaterThan(CRUISE.turnRate * 0.9);
  });

  it('slows smoothly when steered toward a planet it is skimming past', () => {
    const ilex = center('ilex');
    const S = safetyRadius(BODIES.ilex);
    // Skim past Ilex 3 km outside its envelope, tangentially, at full speed.
    const p = ilex.clone().add(new Vector3(-150000, S + 3000, 0));
    const c = new CruiseController();
    c.begin(p, facing(p, p.clone().add(new Vector3(1, 0, 0))), new Vector3(CRUISE.maxSpeed, 0, 0));
    expect(c.speed).toBeCloseTo(CRUISE.maxSpeed, 3);
    let minClear = Infinity;
    let exit = null;
    for (let i = 0; i < 60 * 60 && !exit; i++) {
      // Keep commanding a dive toward the planet.
      exit = c.step(SIM_DT, { ...IDLE, pitch: -1 }).exit;
      minClear = Math.min(minClear, envelopeClearance(c.pos));
    }
    expect(exit).toBe('approach');
    expect(minClear).toBeGreaterThan(0);
    expect(c.safetyStops).toBe(0);
  });

  it('refuses a turn that would put an envelope inside the stopping distance', () => {
    const ilex = center('ilex');
    const S = safetyRadius(BODIES.ilex);
    // Heading +x, 20 km before grazing the top of the envelope by 10 m.
    const p = ilex.clone().add(new Vector3(-20000, S + 10, 0));
    const c = new CruiseController();
    c.begin(p, facing(p, p.clone().add(new Vector3(1, 0, 0))), new Vector3(CRUISE.maxSpeed, 0, 0));
    let minClear = Infinity;
    for (let i = 0; i < 60 * 3; i++) {
      c.step(SIM_DT, { ...IDLE, pitch: -1 });
      minClear = Math.min(minClear, envelopeClearance(c.pos));
    }
    expect(c.refusedTurns).toBeGreaterThan(0);
    expect(minClear).toBeGreaterThan(0);
    expect(c.safetyStops).toBe(0);
  });

  it('the exact segment test stops a ship that is too fast for the free distance', () => {
    const ilex = center('ilex');
    const S = safetyRadius(BODIES.ilex);
    const p = ilex.clone().add(new Vector3(0, S + 200, 0));
    const c = new CruiseController();
    c.begin(p, facing(p, ilex), new Vector3());
    c.speed = CRUISE.maxSpeed; // inconsistent state on purpose: 200 m from the envelope at 15 km/s
    const r = c.step(SIM_DT, IDLE);
    expect(r.exit).toBe('safety');
    expect(c.safetyStops).toBe(1);
    expect(envelopeClearance(c.pos)).toBeGreaterThanOrEqual(0);
    expect(c.speed).toBeLessThanOrEqual(CRUISE.exitSpeed);
  });

  it('free distance matches a brute-force march', () => {
    const p = new Vector3(200000, 50000, -150000);
    const d = center('vesper').sub(p).normalize();
    const fd = freeDistance(p, d);
    let t = 0;
    while (envelopeClearance(p.clone().addScaledVector(d, t)) > 0 && t < 2e6) t += 50;
    expect(Math.abs(fd.distance - t)).toBeLessThan(60);
    expect(fd.body).toBe('vesper');
  });

  it('is independent of the render frame rate', () => {
    const run = (frameDt: number) => {
      const p = new Vector3(300000, 400000, 0);
      const c = new CruiseController();
      c.begin(p, facing(p, p.clone().add(new Vector3(1, 0.2, 0))), new Vector3());
      const stepper = new FixedStepper(SIM_DT, 4, 0.25);
      let steps = 0;
      while (steps < 600) {
        stepper.advance(frameDt, () => {
          if (steps >= 600) return;
          const t = steps * SIM_DT;
          c.step(SIM_DT, { ...IDLE, yaw: t > 3 && t < 6 ? 0.5 : 0, brake: t > 8 });
          steps++;
        });
      }
      return c.pos.clone();
    };
    const a = run(1 / 30);
    const b = run(1 / 144);
    expect(a.distanceTo(b)).toBeLessThan(1e-6);
  });
});
