import { beforeAll, describe, expect, it } from 'vitest';
import { Vector3 } from 'three';
import { Blink, type BlinkSense } from '../src/abilities/blink';
import { ABILITIES } from '../src/abilities/catalog';
import type { BlinkParams } from '../src/abilities/types';
import { initPhysics, Physics, RAPIER, GROUPS } from '../src/physics/Physics';
import { Player, FOOT_OFFSET } from '../src/player/Player';
import { WALK } from '../src/game/config';

const P = (ABILITIES['lunar-step'] as { params: BlinkParams }).params;
const UP = new Vector3(0, 1, 0);
const FWD = new Vector3(0, 0, -1);

beforeAll(async () => {
  await initPhysics();
});

function world(build: (ph: Physics) => void = () => {}) {
  const physics = new Physics();
  const add = (c: [number, number, number], h: [number, number, number]) => {
    const b = physics.world.createRigidBody(RAPIER.RigidBodyDesc.fixed().setTranslation(...c));
    physics.world.createCollider(RAPIER.ColliderDesc.cuboid(...h).setCollisionGroups(GROUPS.terrain), b);
  };
  add([0, -1, -100], [100, 1, 120]);
  build(physics);
  physics.refreshQueries();
  const player = new Player(physics, new Vector3(0, FOOT_OFFSET + WALK.skin + 0.01, 0), UP, FWD);
  return { physics, player, add };
}

function aimAt(pitchDeg: number, yaw = 0): Vector3 {
  const p = (pitchDeg * Math.PI) / 180;
  return new Vector3(-Math.sin(yaw) * Math.cos(p), Math.sin(p), -Math.cos(yaw) * Math.cos(p));
}

function sense(player: Player, aim: Vector3, ready: (p: Vector3) => boolean = () => true): BlinkSense {
  return {
    up: UP,
    eye: player.eye(1, new Vector3()),
    aim,
    grounded: true,
    ray: (o, d, max) => {
      const hit = (player as any).physics.castRay(o.x, o.y, o.z, d.x, d.y, d.z, max, GROUPS.queryWalk);
      return hit ? { dist: hit.toi, normal: new Vector3(hit.nx, hit.ny, hit.nz) } : null;
    },
    groundBelow: (pt, max) => {
      const hit = (player as any).physics.castRay(pt.x, pt.y, pt.z, 0, -1, 0, max, GROUPS.queryWalk);
      return hit ? hit.toi : null;
    },
    fits: (feet) => player.fitsAt(feet),
    ready,
  };
}

describe('blink primitive (Lunar Step tunables) on real colliders', () => {
  it('steps to the ground point under the aim within range, arriving on the ground', () => {
    const { player } = world();
    const b = new Blink(P);
    // Eye at 1.62 m looking 4 degrees down hits the ground ~23 m ahead.
    const t = b.target(sense(player, aimAt(-4)));
    expect(t.ok).toBe(true);
    expect(t.feet.y).toBeGreaterThan(0);
    expect(t.feet.y).toBeLessThan(0.1);
    expect(-t.feet.z).toBeGreaterThan(20);
    expect(b.commit(t)).toBe(true);
    expect(b.cooldown).toBeCloseTo(P.cooldown, 6);
    player.dispose();
  });

  it('refuses aiming at the sky or past the range, consuming nothing', () => {
    const { player } = world();
    const b = new Blink(P);
    const up = b.target(sense(player, aimAt(20)));
    expect(up.ok).toBe(false);
    expect(up.reason).toBe('no target');
    // Level aim: the point at 60 m is 1.6 m above the ground: allowed (within 2 m), arriving on the ground at range.
    const level = b.target(sense(player, aimAt(0)));
    expect(level.ok).toBe(true);
    expect(level.distance).toBeLessThanOrEqual(P.range + 0.5);
    expect(b.commit(up)).toBe(false);
    expect(b.cooldown).toBe(0);
    player.dispose();
  });

  it('stops short of a wall, never inside it', () => {
    const { player } = world((ph) => {
      const w = ph.world.createRigidBody(RAPIER.RigidBodyDesc.fixed().setTranslation(0, 5, -21));
      ph.world.createCollider(RAPIER.ColliderDesc.cuboid(20, 5, 1).setCollisionGroups(GROUPS.terrain), w);
    });
    const b = new Blink(P);
    const t = b.target(sense(player, aimAt(0)));
    expect(t.ok).toBe(true);
    expect(t.feet.z).toBeGreaterThan(-20 + WALK.radius - 1e-3);
    expect(player.fitsAt(t.feet)).toBe(true);
    player.dispose();
  });

  it('refuses a target where the capsule does not fit (low overhang)', () => {
    const { player } = world((ph) => {
      // A slab 1.2 m above the ground from z = -15 to -35.
      const w = ph.world.createRigidBody(RAPIER.RigidBodyDesc.fixed().setTranslation(0, 1.4, -25));
      ph.world.createCollider(RAPIER.ColliderDesc.cuboid(20, 0.2, 10).setCollisionGroups(GROUPS.terrain), w);
    });
    const b = new Blink(P);
    // Aim under the slab's front edge at the ground beneath it.
    const t = b.target(sense(player, aimAt(-5.5)));
    expect(t.ok).toBe(false);
    expect(['blocked', 'no line of sight', 'no ground']).toContain(t.reason);
    player.dispose();
  });
});

describe('blink checks (charter J) with a scripted world', () => {
  const base = (over: Partial<BlinkSense> = {}): BlinkSense => ({
    up: UP,
    eye: new Vector3(0, 1.62, 0),
    aim: new Vector3(0, -0.06, -1).normalize(),
    grounded: true,
    ray: (_o, d, max) => (d.y < 0 ? { dist: Math.min(max, 1.62 / -d.y), normal: UP.clone() } : null),
    groundBelow: (p) => p.y,
    fits: () => true,
    ready: () => true,
    ...over,
  });

  it('needs line of sight, loaded collision and a finished cooldown', () => {
    const b = new Blink(P);
    expect(b.target(base()).ok).toBe(true);
    // Something between the eye and the target's chest.
    let calls = 0;
    const blocked = b.target(
      base({
        ray: (_o, d, max) => {
          calls++;
          if (calls === 1) return { dist: 1.62 / 0.06, normal: UP.clone() };
          return { dist: Math.min(max, 5), normal: new Vector3(0, 0, 1) };
        },
      }),
    );
    expect(blocked.reason).toBe('no line of sight');
    expect(b.target(base({ ready: () => false })).reason).toBe('not loaded');
    expect(b.target(base({ fits: () => false })).reason).toBe('blocked');
    const t = b.target(base());
    expect(b.commit(t)).toBe(true);
    expect(b.target(base()).reason).toBe('cooldown');
    b.tick(P.cooldown - 0.01);
    expect(b.target(base()).reason).toBe('cooldown');
    b.tick(0.02);
    expect(b.target(base()).ok).toBe(true);
  });

  it('lets an airborne blinker arrive up to 3 m above the ground', () => {
    const b = new Blink(P);
    // Aim level from 4 m up: the target is 2.5 m above the ground.
    const s = base({ eye: new Vector3(0, 2.5, 0), aim: FWD.clone(), ray: () => null, groundBelow: (p) => p.y });
    expect(b.target({ ...s, grounded: true }).reason).toBe('no target');
    const air = b.target({ ...s, grounded: false });
    expect(air.ok).toBe(true);
    expect(air.feet.y).toBeCloseTo(2.5, 6);
  });
});
