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

function box(physics: Physics, center: [number, number, number], half: [number, number, number], rotX = 0, group: number = GROUPS.terrain): void {
  const q = new Quaternion().setFromAxisAngle(new Vector3(1, 0, 0), rotX);
  const b = physics.world.createRigidBody(RAPIER.RigidBodyDesc.fixed().setTranslation(...center).setRotation({ x: q.x, y: q.y, z: q.z, w: q.w }));
  physics.world.createCollider(RAPIER.ColliderDesc.cuboid(...half).setCollisionGroups(group), b);
}

function sense(player: Player, heading = FWD, ready: (d: number) => boolean = () => true): SpeedSense {
  const under = player.groundAt(player.feet(new Vector3()), 0.5, 1.0);
  return {
    up: player.up,
    heading,
    grounded: player.grounded,
    normal: under ? under.normal.clone() : null,
    clear: (dir, dist, normal) => player.sweepCapsule(dir, dist, 0.4, normal),
    ground: (dir, d, top, bottom) => {
      const g = player.groundAt(player.feet(new Vector3()).addScaledVector(dir, d), top, -bottom, true);
      return g ? { h: g.h, slopeDeg: (Math.acos(Math.min(1, g.normal.dot(player.up))) * 180) / Math.PI } : null;
    },
    ready,
    gravity: G,
  };
}

/**
 * Run with Q held (until `release` s), then released; returns the trace,
 * including the largest one-step speed drop (charter J: braking is never
 * faster than the brake rate) and the speed when it came to rest.
 */
function run(physics: Physics, player: Player, seconds: number, opts: { release?: number; heading?: Vector3; ready?: (d: number, t: number, z: number) => boolean } = {}) {
  const sp = new Speed(P);
  sp.start(player.vel, sense(player, opts.heading));
  let maxSpeed = 0;
  let minZ = Infinity;
  let state = 'running';
  let t = 0;
  let doneAt = -1;
  let maxDrop = 0;
  let prev = 0;
  for (; t < seconds; t += SIM_DT) {
    const tt = t;
    const ready = opts.ready ? (d: number) => opts.ready!(d, tt, player.pos.z) : undefined;
    const r = sp.step(SIM_DT, { run: opts.release === undefined || t < opts.release, brake: false }, sense(player, opts.heading, ready));
    state = r;
    player.moveFree(SIM_DT, sp.vel, CENTER, sp.snap(SIM_DT));
    physics.step();
    // As the power does: a wall that was not foreseen takes the speed it blocked.
    if (player.hitWall) sp.blocked(Math.hypot(player.vel.length(), player.vVert));
    // Under sprint speed a stop is a walking-pace stop: the bound applies above it.
    if (prev > SPEED_EXIT_MAX) maxDrop = Math.max(maxDrop, prev - sp.speed);
    prev = sp.speed;
    maxSpeed = Math.max(maxSpeed, sp.speed);
    minZ = Math.min(minZ, player.pos.z);
    if (r === 'done') {
      doneAt = t;
      break;
    }
  }
  return { sp, maxSpeed, minZ, state, doneAt, maxDrop };
}

/**
 * Ground along a height profile (x within +-60 m), as a trimesh like real
 * terrain: points (z, y), z decreasing ahead. Joins are smooth by construction.
 */
function profile(physics: Physics, pts: [number, number][]): void {
  const v: number[] = [];
  const idx: number[] = [];
  pts.forEach(([z, y], i) => {
    v.push(-60, y, z, 60, y, z);
    if (i > 0) {
      const a = 2 * (i - 1);
      idx.push(a, a + 1, a + 2, a + 1, a + 3, a + 2);
    }
  });
  const b = physics.world.createRigidBody(RAPIER.RigidBodyDesc.fixed());
  physics.world.createCollider(RAPIER.ColliderDesc.trimesh(new Float32Array(v), new Uint32Array(idx)).setCollisionGroups(GROUPS.terrain), b);
}

/** Braking never exceeds the brake rate in one step (a small allowance for the curve's discretisation). */
const BRAKE_STEP = P.brake * SIM_DT + 0.05;

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
    // Seen in time and braked at the brake rate: no step cuts the speed harder.
    expect(r.maxDrop).toBeLessThanOrEqual(BRAKE_STEP);
    player.dispose();
  });

  it('stops at the foot of a slope steeper than the limit', () => {
    // A 45 degree hillside rising ahead from z = -300 (terrain-like trimesh).
    const { physics, player } = world(300, (ph) => profile(ph, [[-280, 0], [-300, 0], [-340, 40]]));
    const r = run(physics, player, 12);
    expect(r.minZ).toBeGreaterThan(-300);
    expect(r.minZ).toBeLessThan(-300 + STOP_MARGIN + 6);
    expect(['slope', 'wall']).toContain(r.sp.obstacleKind);
    expect(r.maxDrop).toBeLessThanOrEqual(BRAKE_STEP);
    player.dispose();
  });

  it('stops short of a rock slab leaning over the run-way (a prop: the capsule sweep finds it, no contact)', () => {
    // A slab 1 m thick at 45 degrees, its underside meeting the ground at
    // z = -319.6 and leaning toward the runner: at head height (1.8 m) it is
    // over z = -317.8.
    const { physics, player } = world(2000, (ph) => box(ph, [0, 0, -320], [60, 0.5, 30], -Math.PI / 4, GROUPS.props));
    const r = run(physics, player, 12);
    expect(r.minZ).toBeGreaterThan(-317.8 + WALK.radius);
    expect(r.minZ).toBeLessThan(-317.8 + STOP_MARGIN + 6);
    expect(r.sp.obstacleKind).toBe('wall');
    expect(r.maxDrop).toBeLessThanOrEqual(BRAKE_STEP);
    player.dispose();
  });

  it('stops before a ledge (the run-way ends above a 20 m drop)', () => {
    const { physics, player } = world(400, (ph) => box(ph, [0, -21, -680], [60, 1, 300]));
    const r = run(physics, player, 12);
    // Edge at z = -380.
    expect(r.minZ).toBeGreaterThan(-380);
    expect(r.sp.obstacleKind).toBe('ledge');
    expect(player.grounded).toBe(true);
    // The edge is placed between probes as the runner closes in: a smooth stop, no staircase of cuts.
    expect(r.maxDrop).toBeLessThanOrEqual(BRAKE_STEP);
    expect(r.minZ).toBeLessThan(-380 + STOP_MARGIN + 6);
    player.dispose();
  });

  it('stops before a descent steeper than the limit (60 degrees), braking smoothly wherever the probes fall', () => {
    // Flat to z = -300, then a 60 degree slope down 40 m (terrain-like trimesh).
    const fall = 40 / Math.tan((60 * Math.PI) / 180);
    const { physics, player } = world(300, (ph) => profile(ph, [[-280, 0], [-300, 0], [-300 - fall, -40], [-1000, -40]]));
    const r = run(physics, player, 12);
    expect(r.minZ).toBeGreaterThan(-300);
    expect(r.minZ).toBeLessThan(-300 + STOP_MARGIN + 6);
    expect(r.sp.obstacleKind).toBe('ledge');
    expect(r.maxDrop).toBeLessThanOrEqual(BRAKE_STEP);
    expect(player.grounded).toBe(true);
    player.dispose();
  });

  it('no ground at all under points said to be loaded (a strip past the last loaded tile) is unloaded collision, not a ledge: limited, never stopped', () => {
    // The run-way ends at z = -380 with nothing below, while readiness reports everything loaded.
    const { physics, player } = world(400);
    const sp = new Speed(P);
    sp.start(player.vel, sense(player));
    const kinds = new Set<string | null>();
    let atEdge = -1;
    for (let t = 0; t < 8 && atEdge < 0; t += SIM_DT) {
      sp.step(SIM_DT, { run: true, brake: false }, sense(player));
      if (sp.obstacle < 60) kinds.add(sp.obstacleKind);
      player.moveFree(SIM_DT, sp.vel, CENTER, sp.snap(SIM_DT));
      physics.step();
      if (player.pos.z < -380) atEdge = sp.speed;
    }
    expect([...kinds]).toEqual(['unloaded']);
    expect(atEdge).toBeGreaterThanOrEqual(SPEED_UNREADY - 1);
    player.dispose();
  });

  it('where collision ahead is not loaded, runs no faster than it can stop within what is loaded, never stalled', () => {
    const { physics, player } = world(2000);
    const r = run(physics, player, 6, { ready: (d) => d < 60 });
    const cap = Math.sqrt(2 * P.brake * (60 - STOP_MARGIN));
    expect(r.maxSpeed).toBeLessThanOrEqual(cap + 1);
    expect(r.maxSpeed).toBeGreaterThan(SPEED_UNREADY);
    expect(r.sp.obstacleKind).toBe('unloaded');
    player.dispose();
  });

  it('at top speed toward collision not yet loaded, it brakes at the brake rate down to the unready speed and carries on', () => {
    const { physics, player } = world(3000);
    // Tiles beyond z = -700 are not loaded (a boundary fixed in the world, approached at speed).
    const r = run(physics, player, 12, { ready: (d, _t, z) => z - d > -700 });
    expect(r.maxSpeed).toBeCloseTo(P.top, 3);
    expect(r.maxDrop).toBeLessThanOrEqual(BRAKE_STEP);
    // Limited, never stalled: past the boundary at the unready speed.
    expect(r.minZ).toBeLessThan(-760);
    expect(r.sp.speed).toBeCloseTo(SPEED_UNREADY, 3);
    player.dispose();
  });

  it('runs up a walkable 20 degree rise from the flat without stopping at its foot', () => {
    // Flat to z = -300, then a 20 degree rise (terrain-like trimesh), longer than the run.
    const t = Math.tan((20 * Math.PI) / 180);
    const { physics, player } = world(300, (ph) => profile(ph, [[-280, 0], [-300, 0], [-900, 600 * t]]));
    const r = run(physics, player, 7);
    expect(r.minZ).toBeLessThan(-380); // well up the ramp
    expect(r.maxDrop).toBeLessThanOrEqual(BRAKE_STEP);
    expect(r.sp.speed).toBeGreaterThan(60);
    player.dispose();
  });

  it('runs down a slope onto a valley floor without stopping at the bottom', () => {
    // Flat to z = -200, a 15 degree descent to z = -400, then a flat floor (terrain-like trimesh).
    const drop = Math.tan((15 * Math.PI) / 180) * 200;
    const { physics, player } = world(200, (ph) => profile(ph, [[-180, 0], [-200, 0], [-400, -drop], [-1400, -drop]]));
    const r = run(physics, player, 9);
    expect(r.minZ).toBeLessThan(-600); // across the floor
    expect(r.maxDrop).toBeLessThanOrEqual(BRAKE_STEP);
    player.dispose();
  });

  it('a landing ends the fall: the next airborne moment starts level', () => {
    const { physics, player } = world(2000);
    const sp = new Speed(P);
    sp.start(player.vel, sense(player));
    // Airborne for a moment (no ground under the feet), then grounded again.
    const s = sense(player);
    sp.step(SIM_DT, { run: true, brake: false }, { ...s, grounded: false, normal: null });
    sp.step(SIM_DT, { run: true, brake: false }, { ...s, grounded: false, normal: null });
    expect(sp.vVert).toBeLessThan(0);
    sp.step(SIM_DT, { run: true, brake: false }, s);
    expect(sp.vVert).toBe(0);
    player.dispose();
    void physics;
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
