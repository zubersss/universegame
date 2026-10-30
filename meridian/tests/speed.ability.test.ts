import { beforeAll, describe, expect, it } from 'vitest';
import { Quaternion, Vector3 } from 'three';
import { Speed, SPEED_UNREADY, STOP_MARGIN, type SpeedSense } from '../src/abilities/speed';
import { ABILITIES } from '../src/abilities/catalog';
import { SPEED_EXIT_MAX, type SpeedParams } from '../src/abilities/types';
import { initPhysics, Physics, RAPIER, GROUPS } from '../src/physics/Physics';
import { Player, FOOT_OFFSET } from '../src/player/Player';
import { SIM_DT, WALK } from '../src/game/config';

const P = (ABILITIES.redline as { params: SpeedParams }).params;
const UP = new Vector3(0, 1, 0);
const FWD = new Vector3(0, 0, -1);
const CENTER = new Vector3(0, -1e7, 0);
const G = 3.71; // Mars

beforeAll(async () => {
  await initPhysics();
});

type Build = (physics: Physics) => void;

/** A flat run-way from z = +20 to z = -length (top at y = 0), plus whatever `build` adds. */
function world(length: number, build: Build = () => {}) {
  const physics = new Physics();
  const ground = physics.world.createRigidBody(RAPIER.RigidBodyDesc.fixed().setTranslation(0, -1, 20 - length / 2));
  physics.world.createCollider(RAPIER.ColliderDesc.cuboid(60, 1, length / 2).setCollisionGroups(GROUPS.terrain), ground);
  build(physics);
  physics.refreshQueries();
  const player = new Player(physics, new Vector3(0, FOOT_OFFSET + WALK.skin + 0.01, 0), UP, FWD);
  const idle = { forward: 0, right: 0, sprint: false, jump: false, yaw: 0, pitch: 0 };
  for (let i = 0; i < 20; i++) {
    player.step(SIM_DT, idle, CENTER, G);
    physics.step();
  }
  return { physics, player };
}

function box(physics: Physics, center: [number, number, number], half: [number, number, number], rotX = 0): void {
  const q = new Quaternion().setFromAxisAngle(new Vector3(1, 0, 0), rotX);
  const b = physics.world.createRigidBody(RAPIER.RigidBodyDesc.fixed().setTranslation(...center).setRotation({ x: q.x, y: q.y, z: q.z, w: q.w }));
  physics.world.createCollider(RAPIER.ColliderDesc.cuboid(...half).setCollisionGroups(GROUPS.terrain), b);
}

function sense(player: Player, heading = FWD, ready: (d: number) => boolean = () => true): SpeedSense {
  const under = player.groundAt(player.feet(new Vector3()), 0.5, 1.0);
  return {
    up: player.up,
    heading,
    grounded: player.grounded,
    normal: under ? under.normal.clone() : null,
    clear: (dir, dist) => player.sweepCapsule(dir, dist, 0.4),
    groundAhead: (dir, d) => {
      const g = player.groundAt(player.feet(new Vector3()).addScaledVector(dir, d), 40, 80);
      return g ? { h: g.h, slopeDeg: (Math.acos(Math.min(1, g.normal.dot(player.up))) * 180) / Math.PI } : null;
    },
    ready,
    gravity: G,
  };
}

/** Run with Q held (until `release` s), then released; returns the trace. */
function run(physics: Physics, player: Player, seconds: number, opts: { release?: number; heading?: Vector3; ready?: (d: number) => boolean } = {}) {
  const sp = new Speed(P);
  sp.start(player.vel, sense(player, opts.heading));
  let maxSpeed = 0;
  let minZ = Infinity;
  let state = 'running';
  let t = 0;
  let doneAt = -1;
  for (; t < seconds; t += SIM_DT) {
    const r = sp.step(SIM_DT, { run: opts.release === undefined || t < opts.release, brake: false }, sense(player, opts.heading, opts.ready));
    state = r;
    player.moveFree(SIM_DT, sp.vel, CENTER, 0.6);
    physics.step();
    maxSpeed = Math.max(maxSpeed, sp.speed);
    minZ = Math.min(minZ, player.pos.z);
    if (r === 'done') {
      doneAt = t;
      break;
    }
  }
  return { sp, maxSpeed, minZ, state, doneAt };
}

describe('speed primitive (Redline tunables) on real colliders', () => {
  it('reaches top speed on the flat, then always brakes down to sprint speed before handing back', () => {
    const { physics, player } = world(2000);
    const r = run(physics, player, 20, { release: 4 });
    expect(r.maxSpeed).toBeCloseTo(P.top, 6);
    expect(r.state).toBe('done');
    // Braking from 110 to 7.5 m/s at 50 m/s^2 takes ~2.05 s after the release.
    expect(r.doneAt - 4).toBeGreaterThan((P.top - SPEED_EXIT_MAX) / P.brake - 0.05);
    expect(r.doneAt - 4).toBeLessThan((P.top - SPEED_EXIT_MAX) / P.brake + 0.1);
    expect(r.sp.speed).toBeLessThanOrEqual(SPEED_EXIT_MAX);
    expect(player.grounded).toBe(true);
    player.dispose();
  });

  it('stops before a wall at full speed (braking curve, no contact, no tunnelling)', () => {
    const { physics, player } = world(2000, (ph) => box(ph, [0, 5, -401], [60, 5, 1]));
    const r = run(physics, player, 12);
    // Wall face at z = -400: stops short of it by about the margin, never touching.
    expect(r.minZ).toBeGreaterThan(-400 + WALK.radius + 0.5);
    expect(r.minZ).toBeLessThan(-400 + WALK.radius + STOP_MARGIN + 6);
    expect(r.sp.obstacleKind).toBe('wall');
    expect(r.maxSpeed).toBeCloseTo(P.top, 3);
    player.dispose();
  });

  it('stops at the foot of a slope steeper than the limit', () => {
    // A 45 degree ramp rising ahead from z = -300.
    const { physics, player } = world(2000, (ph) => box(ph, [0, 0, -300 - 20], [60, 0.5, 30], -Math.PI / 4));
    const r = run(physics, player, 12);
    expect(r.minZ).toBeGreaterThan(-300 - 4);
    expect(['slope', 'wall']).toContain(r.sp.obstacleKind);
    player.dispose();
  });

  it('stops before a ledge (the run-way ends above a 20 m drop)', () => {
    const { physics, player } = world(400, (ph) => box(ph, [0, -21, -700], [60, 1, 300]));
    const r = run(physics, player, 12);
    // Edge at z = -380.
    expect(r.minZ).toBeGreaterThan(-380);
    expect(r.sp.obstacleKind).toBe('ledge');
    expect(player.grounded).toBe(true);
    player.dispose();
  });

  it('limits its speed where collision ahead is not loaded', () => {
    const { physics, player } = world(2000);
    const r = run(physics, player, 6, { ready: (d) => d < 60 });
    expect(r.maxSpeed).toBeLessThanOrEqual(SPEED_UNREADY);
    player.dispose();
  });

  it('steers with the look, slower at speed', () => {
    const { physics, player } = world(2000);
    const sp = new Speed(P);
    sp.start(player.vel, sense(player));
    const right = new Vector3(1, 0, 0);
    // From rest: the course turns at ~3 rad/s.
    sp.step(SIM_DT * 6, { run: true, brake: false }, sense(player, right));
    expect(Math.acos(sp.course.dot(FWD))).toBeGreaterThan(P.yawLow * SIM_DT * 6 * 0.8);
    // At top speed: ~0.8 rad/s.
    sp.speed = P.top;
    sp.course.copy(FWD);
    sp.step(0.1, { run: true, brake: false }, sense(player, right));
    expect(Math.acos(sp.course.dot(FWD))).toBeCloseTo(P.yawHigh * 0.1, 2);
    player.dispose();
    void physics;
  });
});
