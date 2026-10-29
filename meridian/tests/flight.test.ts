import { beforeAll, describe, expect, it } from 'vitest';
import { Vector3 } from 'three';
import { GROUPS, initPhysics, Physics, RAPIER } from '../src/physics/Physics';
import { ShipSim } from '../src/ship/Ship';
import { FixedStepper } from '../src/core/loop';
import { FlightEnvProvider } from '../src/world/FlightEnvProvider';
import { BODIES } from '../src/world/bodies';
import { FLIGHT, MAX_FRAME_GAP, MAX_STEPS_PER_FRAME, SIM_DT } from '../src/game/config';
import { NO_CONTROLS, type FlightOutput, type ShipControls } from '../src/ship/FlightModel';
import { mulberry32 } from '../src/core/rng';
import { quatFromForwardUp } from '../src/core/mathx';

beforeAll(async () => {
  await initPhysics();
});

interface Rig {
  physics: Physics;
  ship: ShipSim;
  env: FlightEnvProvider;
  steps: number;
}

/** Ilex as a smooth ball collider, ship hovering 40 m above it (origin near the ship). */
function makeRig(): Rig {
  const def = BODIES.ilex;
  const physics = new Physics();
  const n = new Vector3(0.3, 0.8, 0.52).normalize();
  const sys = n.clone().multiplyScalar(def.radius + 40);
  const origin = new Vector3(Math.round(sys.x / 1024) * 1024, Math.round(sys.y / 1024) * 1024, Math.round(sys.z / 1024) * 1024);
  const centerLocal = new Vector3(-origin.x, -origin.y, -origin.z);
  const ground = physics.world.createRigidBody(RAPIER.RigidBodyDesc.fixed().setTranslation(centerLocal.x, centerLocal.y, centerLocal.z));
  physics.world.createCollider(RAPIER.ColliderDesc.ball(def.radius).setCollisionGroups(GROUPS.terrain).setSolverGroups(GROUPS.terrain), ground);
  const fwd = new Vector3(1, 0, 0).addScaledVector(n, -n.x).normalize();
  const ship = new ShipSim(physics, sys.clone().sub(origin), quatFromForwardUp(fwd, n));
  physics.refreshQueries();
  const env = new FlightEnvProvider(def, centerLocal, origin, () => 0);
  return { physics, ship, env, steps: 0 };
}

const out: FlightOutput = { force: new Vector3(), angvel: new Vector3() };

function step(rig: Rig, c: ShipControls): void {
  const { ship, env, physics } = rig;
  ship.beginStep();
  env.update(ship.currPos);
  ship.flight.step(SIM_DT, { pos: ship.currPos, vel: ship.vel, quat: ship.currQuat, angvel: ship.angvel }, c, env, out);
  ship.applyControl(out.force, out.angvel);
  ship.updateGearColliders();
  physics.step();
  ship.syncFromBody();
  rig.steps++;
}

/** Scripted control timeline expressed in simulation time. */
function script(t: number): ShipControls {
  const c: ShipControls = { ...NO_CONTROLS };
  if (t < 4) c.throttleAxis = 1;
  if (t >= 2 && t < 3) c.pitch = 0.6;
  if (t >= 3 && t < 4.5) c.yaw = -0.8;
  if (t >= 4.5 && t < 5.5) c.roll = 1;
  if (t >= 5 && t < 7) c.vertical = 1;
  if (t >= 7 && t < 9) c.boost = true;
  if (t >= 9 && t < 10) c.brake = true;
  return c;
}

function runWithFrames(frameDt: (i: number) => number, totalSteps: number): Rig {
  const rig = makeRig();
  const stepper = new FixedStepper(SIM_DT, MAX_STEPS_PER_FRAME, MAX_FRAME_GAP);
  let frame = 0;
  while (rig.steps < totalSteps) {
    stepper.advance(frameDt(frame++), () => {
      if (rig.steps < totalSteps) step(rig, script(rig.steps * SIM_DT));
    });
    if (frame > 1e6) throw new Error('runaway loop');
  }
  return rig;
}

describe('assisted flight (fixed step)', () => {
  it('produces the same trajectory regardless of render frame rate', () => {
    const N = 600; // 10 s of simulation
    const a = runWithFrames(() => 1 / 60, N);
    const b = runWithFrames(() => 1 / 30, N);
    const c = runWithFrames(() => 1 / 144, N);
    const rnd = mulberry32(7);
    const d = runWithFrames(() => 0.004 + rnd() * 0.05, N); // jittery 20–250 fps, never above the step cap
    const tol = 1e-6; // meters / m/s — stated tolerance
    for (const other of [b, c, d]) {
      expect(other.ship.currPos.distanceTo(a.ship.currPos)).toBeLessThan(tol);
      expect(other.ship.vel.distanceTo(a.ship.vel)).toBeLessThan(tol);
      expect(Math.abs(other.ship.currQuat.dot(a.ship.currQuat))).toBeGreaterThan(1 - 1e-9);
    }
    // Sanity: the script actually moved and turned the ship.
    expect(a.ship.currPos.length()).toBeGreaterThan(200);
  });

  it('does not simulate catch-up after a long frame gap', () => {
    const stepper = new FixedStepper(SIM_DT, MAX_STEPS_PER_FRAME, MAX_FRAME_GAP);
    let steps = 0;
    stepper.advance(60, () => steps++); // a minute-long gap (tab switch)
    expect(steps).toBeLessThanOrEqual(MAX_STEPS_PER_FRAME);
    stepper.advance(1 / 60, () => steps++);
    expect(steps).toBeLessThanOrEqual(MAX_STEPS_PER_FRAME + 2);
  });

  it('holds altitude while accelerating hard (gravity compensation first)', () => {
    const rig = makeRig();
    const env = rig.env.update(rig.ship.currPos);
    const alt0 = env.altitude;
    for (let i = 0; i < 300; i++) step(rig, { ...NO_CONTROLS, throttleAxis: 1 });
    const alt1 = rig.env.update(rig.ship.currPos).altitude;
    expect(Math.abs(alt1 - alt0)).toBeLessThan(2.5);
    expect(rig.ship.speed).toBeGreaterThan(100);
    expect(rig.ship.speed).toBeLessThan(FLIGHT.capLow + 5);
  });

  it('brakes to a stop and hovers', () => {
    const rig = makeRig();
    for (let i = 0; i < 360; i++) step(rig, { ...NO_CONTROLS, throttleAxis: 1 });
    for (let i = 0; i < 240; i++) step(rig, { ...NO_CONTROLS, brake: true });
    expect(rig.ship.speed).toBeLessThan(0.5);
    expect(rig.ship.flight.throttle).toBe(0);
  });

  it('survives three minutes of random input with ground strikes: no NaN, no runaway', () => {
    const rig = makeRig();
    const rnd = mulberry32(42);
    let c: ShipControls = { ...NO_CONTROLS };
    let maxSpeed = 0;
    let minClear = Infinity;
    for (let i = 0; i < 180 * 60; i++) {
      if (i % 45 === 0) {
        c = {
          pitch: rnd() * 2 - 1,
          yaw: rnd() * 2 - 1,
          roll: rnd() < 0.3 ? rnd() * 2 - 1 : 0,
          throttleAxis: rnd() < 0.6 ? 1 : rnd() < 0.5 ? -1 : 0,
          vertical: rnd() < 0.4 ? -1 : rnd() < 0.3 ? 1 : 0, // biased downward: hits the ground
          boost: rnd() < 0.2,
          brake: rnd() < 0.08,
        };
      }
      step(rig, c);
      const s = rig.ship;
      expect(Number.isFinite(s.currPos.x + s.currPos.y + s.currPos.z + s.vel.x + s.vel.y + s.vel.z)).toBe(true);
      maxSpeed = Math.max(maxSpeed, s.speed);
      const env = rig.env.update(s.currPos);
      minClear = Math.min(minClear, env.clearance);
    }
    // Never faster than the space boost cap; never tunnels through the ground.
    expect(maxSpeed).toBeLessThan(FLIGHT.capSpaceBoost * 1.05);
    console.log(`soak: maxSpeed=${maxSpeed.toFixed(1)} minClearance=${minClear.toFixed(3)}`);
    // The hull belly sits ~1 m below the ship origin; deeper means tunneling.
    expect(minClear).toBeGreaterThan(0.5);
  });
  it('reaches the open-space caps (900 m/s, 1,800 m/s with boost) without exceeding them', () => {
    // Far above Ilex (no terrain within reach): open space flight.
    const def = BODIES.ilex;
    const run = (boost: boolean) => {
      const physics = new Physics();
      const n = new Vector3(0.3, 0.8, 0.52).normalize();
      const sys = n.clone().multiplyScalar(def.radius * 2.2);
      const centerLocal = sys.clone().negate();
      const ship = new ShipSim(physics, new Vector3(), quatFromForwardUp(n, new Vector3(1, 0, 0)));
      const env = new FlightEnvProvider(def, centerLocal, sys, () => 0);
      const rig: Rig = { physics, ship, env, steps: 0 };
      let max = 0;
      for (let i = 0; i < 60 * 40; i++) {
        step(rig, { ...NO_CONTROLS, throttleAxis: 1, boost });
        max = Math.max(max, ship.speed);
      }
      return { final: ship.speed, max };
    };
    const normal = run(false);
    const boosted = run(true);
    console.log(`space caps: normal ${normal.final.toFixed(1)} (max ${normal.max.toFixed(1)}), boost ${boosted.final.toFixed(1)} (max ${boosted.max.toFixed(1)})`);
    expect(normal.final).toBeGreaterThan(FLIGHT.capSpace * 0.97);
    expect(normal.max).toBeLessThan(FLIGHT.capSpace * 1.01);
    expect(boosted.final).toBeGreaterThan(FLIGHT.capSpaceBoost * 0.97);
    expect(boosted.max).toBeLessThan(FLIGHT.capSpaceBoost * 1.01);
  });
});
