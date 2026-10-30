import { beforeAll, describe, expect, it } from 'vitest';
import { Vector3 } from 'three';
import { Flight, FLIGHT_TAKEOFF_CLIMB, FLIGHT_UNREADY_SPEED, type FlightInput, type FlightSense } from '../src/abilities/flight';
import { ABILITIES } from '../src/abilities/catalog';
import type { FlightParams } from '../src/abilities/types';
import { initPhysics, Physics, RAPIER, GROUPS } from '../src/physics/Physics';
import { Player, FOOT_OFFSET } from '../src/player/Player';
import { SIM_DT, WALK } from '../src/game/config';

const P = (ABILITIES['skyborne-flight'] as { params: FlightParams }).params;
const UP = new Vector3(0, 1, 0);
const FWD = new Vector3(0, 0, -1);
const NONE: FlightInput = { climb: false, descend: false, faster: false, slower: false, boost: false, brake: false };
const sense = (over: Partial<FlightSense> = {}): FlightSense => ({ up: UP, heading: FWD, height: 50, grounded: false, ready: true, ...over });

function run(f: Flight, seconds: number, inp: Partial<FlightInput>, s: Partial<FlightSense> = {}): 'flying' | 'landed' {
  let r: 'flying' | 'landed' = 'flying';
  for (let t = 0; t < seconds - 1e-9; t += SIM_DT) {
    r = f.step(SIM_DT, { ...NONE, ...inp }, sense(s));
    if (r === 'landed') break;
  }
  return r;
}

beforeAll(async () => {
  await initPhysics();
});

describe('flight primitive (Skyborne Flight tunables)', () => {
  it('takes off rising, carrying the walking speed', () => {
    const f = new Flight(P);
    f.start(new Vector3(0, 0, -4.5), sense({ height: 0.5 }));
    expect(f.vel.y).toBeCloseTo(FLIGHT_TAKEOFF_CLIMB, 6);
    expect(f.speed).toBeCloseTo(4.5, 6);
    // Right after take-off it does not count as landing even though it is low and slow.
    expect(f.step(SIM_DT, NONE, sense({ height: 0.6 }))).toBe('flying');
  });

  it('speeds up at the acceleration to cruise, and only boost goes beyond', () => {
    const f = new Flight(P);
    f.start(new Vector3(), sense());
    run(f, 2, { faster: true });
    expect(f.speed).toBeCloseTo(P.accel * 2, 0);
    run(f, 6, { faster: true });
    expect(f.speed).toBeCloseTo(P.cruise, 6);
    expect(-f.vel.z).toBeGreaterThan(P.cruise - 1);
    run(f, 10, { faster: true, boost: true });
    expect(f.speed).toBeCloseTo(P.boost, 6);
    expect(f.vel.length()).toBeGreaterThan(P.boost - 2);
    // Releasing boost settles back to cruise.
    run(f, 8, {});
    expect(f.speed).toBeCloseTo(P.cruise, 6);
  });

  it('brakes to a hover and holds its height', () => {
    const f = new Flight(P);
    f.start(new Vector3(), sense());
    run(f, 6, { faster: true, climb: true });
    expect(f.vel.y).toBeCloseTo(P.climb, 1);
    run(f, (P.cruise / P.brake) * 1.6, { brake: true });
    expect(f.vel.length()).toBeLessThan(0.05);
    run(f, 2, {});
    expect(Math.abs(f.vel.y)).toBeLessThan(1e-9); // hover: no sinking
  });

  it('turns its course toward the camera heading at the limited rate', () => {
    const f = new Flight(P);
    f.start(new Vector3(0, 0, -P.cruise), sense());
    const right = new Vector3(1, 0, 0);
    run(f, 0.5, {}, { heading: right });
    const angle = Math.acos(Math.min(1, f.course.dot(FWD)));
    expect(angle).toBeCloseTo(P.turn * 0.5, 2);
    run(f, 2, {}, { heading: right });
    expect(f.course.dot(right)).toBeGreaterThan(0.999);
  });

  it('is pushed down above the ceiling and slowed where collision is not loaded', () => {
    const f = new Flight(P);
    f.start(new Vector3(), sense());
    run(f, 3, { climb: true }, { height: P.ceiling + 60 });
    expect(f.vel.y).toBeLessThan(-1);
    const g = new Flight(P);
    g.start(new Vector3(), sense());
    run(g, 8, { faster: true, boost: true }, { ready: false });
    expect(g.speed).toBeLessThanOrEqual(FLIGHT_UNREADY_SPEED);
  });

  it('lands only near the ground, slowly and not climbing: never in mid-air', () => {
    const f = new Flight(P);
    f.start(new Vector3(), sense({ height: 10 }));
    // High above the ground and slow: keeps flying (hover), however long.
    expect(run(f, 5, {}, { height: 10 })).toBe('flying');
    // Low but fast: keeps flying.
    const g = new Flight(P);
    g.start(new Vector3(0, 0, -30), sense({ height: 1 }));
    g.speed = 30;
    expect(run(g, 1, {}, { height: 1 })).toBe('flying');
    // Low, slow, descending: lands.
    expect(run(f, 3, { descend: true }, { height: 1.2 })).toBe('landed');
    // Touching the ground while slow also lands; climbing never does.
    const h = new Flight(P);
    h.start(new Vector3(), sense());
    run(h, 1, {});
    expect(run(h, 1, { climb: true }, { height: 0.2, grounded: true })).toBe('flying');
  });
});

describe('powered movement through the character controller', () => {
  it('flies into a wall at boost speed without passing through it', () => {
    const physics = new Physics();
    const ground = physics.world.createRigidBody(RAPIER.RigidBodyDesc.fixed().setTranslation(0, -1, 0));
    physics.world.createCollider(RAPIER.ColliderDesc.cuboid(200, 1, 200).setCollisionGroups(GROUPS.terrain), ground);
    // A 2 m thick wall 40 m ahead, from the ground up to 60 m.
    const wall = physics.world.createRigidBody(RAPIER.RigidBodyDesc.fixed().setTranslation(0, 30, -41));
    physics.world.createCollider(RAPIER.ColliderDesc.cuboid(50, 30, 1).setCollisionGroups(GROUPS.terrain), wall);
    physics.refreshQueries();
    const player = new Player(physics, new Vector3(0, 10 + FOOT_OFFSET, 0), UP, FWD);
    const center = new Vector3(0, -1e7, 0);
    const f = new Flight(P);
    f.start(new Vector3(), sense());
    f.speed = P.boost;
    f.vel.set(0, 0, -P.boost);
    let minZ = 0;
    for (let i = 0; i < 120; i++) {
      f.step(SIM_DT, { ...NONE, faster: true, boost: true }, sense({ height: player.pos.y - FOOT_OFFSET }));
      player.moveFree(SIM_DT, f.vel, center);
      physics.step();
      minZ = Math.min(minZ, player.pos.z);
    }
    // The wall's near face is at z = -40; the capsule (radius 0.35) stops on this side.
    expect(minZ).toBeGreaterThan(-40 + WALK.radius - 0.05);
    // Blocked motion shows in the walker's velocity (collision demand and animation read it).
    expect(Math.abs(player.vel.z)).toBeLessThan(1);
    player.dispose();
  });
});
