import { beforeAll, describe, expect, it } from 'vitest';
import { Vector3 } from 'three';
import { AbilityController, type AbilityHud } from '../src/abilities/AbilityController';
import type { PowerWorld } from '../src/abilities/powers';
import { ABILITIES } from '../src/abilities/catalog';
import { SPEED_EXIT_MAX, type BlinkParams, type FlightParams, type SpeedParams } from '../src/abilities/types';
import { initPhysics, Physics, RAPIER, GROUPS } from '../src/physics/Physics';
import { Player, FOOT_OFFSET, type WalkInput } from '../src/player/Player';
import { SIM_DT, WALK } from '../src/game/config';
import type { AbilitySlot } from '../src/ui/Hud';

const UP = new Vector3(0, 1, 0);
const FWD = new Vector3(0, 0, -1);
const CENTER = new Vector3(0, -1e7, 0);

beforeAll(async () => {
  await initPhysics();
});

/** A flat world, a walker and the controller, stepped the way Game steps ON_FOOT. */
function rig(body: string, power: string, gravity: number) {
  const physics = new Physics();
  const ground = physics.world.createRigidBody(RAPIER.RigidBodyDesc.fixed().setTranslation(0, -1, -500));
  physics.world.createCollider(RAPIER.ColliderDesc.cuboid(800, 1, 800).setCollisionGroups(GROUPS.terrain), ground);
  physics.refreshQueries();
  const player = new Player(physics, new Vector3(0, FOOT_OFFSET + WALK.skin + 0.01, 0), UP, FWD);
  const slots: (AbilitySlot | null)[] = [];
  const warnings: (string | null)[] = [];
  const hud: AbilityHud = { setAbility: (s) => slots.push(s), setWarning: (t) => warnings.push(t) };
  const ctl = new AbilityController(hud, () => 'walk', () => 0);
  ctl.enter({ body, power: power as never });
  const heldKeys = new Set<string>();
  const presses = new Set<string>();
  const idle: WalkInput = { forward: 0, right: 0, sprint: false, jump: false, yaw: 0, pitch: 0 };
  const world = (walk: WalkInput): PowerWorld => ({
    player,
    held: (c) => heldKeys.has(c),
    pressed: (c) => presses.delete(c),
    walk,
    center: CENTER,
    gravity,
    ready: () => true,
  });
  const states: string[] = [];
  const step = (walk: Partial<WalkInput> = {}) => {
    const w = { ...idle, ...walk };
    const owned = ctl.step(SIM_DT, world(w));
    if (!owned) player.step(SIM_DT, w, CENTER, gravity);
    physics.step();
    states.push(ctl.state);
  };
  const height = () => player.pos.y - FOOT_OFFSET;
  return { physics, player, ctl, heldKeys, presses, step, states, slots, warnings, height };
}

describe('powers driven through the ability controller (charter K controls)', () => {
  it('Skyborne Flight: hold Space to take off, fly, and land only when low and slow', () => {
    const r = rig('earth', 'skyborne-flight', 9.81);
    const P = (ABILITIES['skyborne-flight'] as { params: FlightParams }).params;
    // Press and hold Space: the first press jumps (walking), holding on takes off.
    r.heldKeys.add('Space');
    r.step({ jump: true });
    for (let i = 0; i < 60; i++) r.step();
    expect(r.ctl.state).toBe('flight');
    expect(r.ctl.log.at(-1)).toMatchObject({ from: 'walk', to: 'flight' });
    // Climb for 3 s, then cruise forward.
    for (let i = 0; i < 180; i++) r.step();
    expect(r.height()).toBeGreaterThan(40);
    r.heldKeys.delete('Space');
    r.heldKeys.add('KeyW');
    for (let i = 0; i < 300; i++) r.step();
    // 5 s at 25 m/s^2 reaches the 90 m/s cruise cap (boost is Shift).
    expect(r.player.vel.length()).toBeGreaterThan(P.cruise - 1);
    expect(r.player.vel.length()).toBeLessThan(P.cruise + 1);
    // Hover: no landing in mid-air however slow.
    r.heldKeys.delete('KeyW');
    r.heldKeys.add('KeyX');
    for (let i = 0; i < 400; i++) r.step();
    expect(r.ctl.state).toBe('flight');
    expect(r.player.vel.length()).toBeLessThan(0.1);
    // Descend and land.
    r.heldKeys.delete('KeyX');
    r.heldKeys.add('ControlLeft');
    let landedAt = -1;
    for (let i = 0; i < 600 && landedAt < 0; i++) {
      const h = r.height();
      r.step();
      if (r.ctl.state === 'walk') landedAt = h;
    }
    expect(landedAt).toBeGreaterThanOrEqual(0);
    expect(landedAt).toBeLessThan(P.landHeight + 0.2); // never ends higher than the landing flare
    r.heldKeys.clear();
    for (let i = 0; i < 60; i++) r.step();
    expect(r.player.grounded).toBe(true);
    // The HUD slot showed the power while it was usable.
    expect(r.slots.some((s) => s?.name === 'Skyborne Flight')).toBe(true);
    r.player.dispose();
  });

  it('Redline: hold Q to run at superspeed, release and it always brakes back to sprint speed', () => {
    const r = rig('mars', 'redline', 3.71);
    const P = (ABILITIES.redline as { params: SpeedParams }).params;
    r.heldKeys.add('KeyQ');
    for (let i = 0; i < 240; i++) r.step();
    expect(r.ctl.state).toBe('speed');
    expect(r.player.vel.length()).toBeGreaterThan(P.top - 1);
    r.heldKeys.delete('KeyQ');
    let walkAt = -1;
    for (let i = 0; i < 300 && walkAt < 0; i++) {
      r.step();
      if (r.ctl.state === 'walk') walkAt = i;
    }
    // Braking 110 -> 7.5 m/s at 50 m/s^2 takes about 2 s.
    expect(walkAt * SIM_DT).toBeGreaterThan(1.9);
    expect(r.player.vel.length()).toBeLessThanOrEqual(SPEED_EXIT_MAX + 0.5);
    r.player.dispose();
  });

  it('Lunar Step: Q steps to the aimed ground with zero velocity; a refused step costs nothing', () => {
    const r = rig('moon', 'lunar-step', 1.62);
    const P = (ABILITIES['lunar-step'] as { params: BlinkParams }).params;
    for (let i = 0; i < 10; i++) r.step();
    // Aim about 4 degrees down: the ground ~23 m ahead.
    r.player.look(0, -0.07);
    const z0 = r.player.pos.z;
    r.presses.add('KeyQ');
    r.step();
    expect(r.player.pos.z).toBeLessThan(z0 - 15);
    expect(r.player.vel.length()).toBe(0);
    expect(r.ctl.log.map((e) => `${e.from}>${e.to}`)).toEqual(['walk>blink', 'blink>walk']);
    // Straight away again: cooling down, refused, red line on the HUD, nothing moves.
    const z1 = r.player.pos.z;
    r.presses.add('KeyQ');
    r.step();
    expect(r.player.pos.z).toBeCloseTo(z1, 3);
    expect(r.warnings.at(-1)).toMatch(/Lunar Step: cooldown/);
    // After the cooldown, aiming at the sky is refused too (no ground there).
    for (let i = 0; i < Math.ceil(P.cooldown / SIM_DT) + 2; i++) r.step();
    r.player.look(0, 0.6);
    r.presses.add('KeyQ');
    r.step();
    expect(r.player.pos.z).toBeCloseTo(z1, 3);
    expect(r.warnings.at(-1)).toMatch(/no target/);
    expect(r.ctl.view()).toMatchObject({ id: 'lunar-step', cooldown: 0 });
    r.player.dispose();
  });
});

describe('superspeed on a slope', () => {
  it('accelerates to top speed up a 20 degree incline (the speed is measured along the ground)', () => {
    const physics = new Physics();
    // A long 20 degree ramp rising ahead (-Z), starting at the origin.
    const ang = (20 * Math.PI) / 180;
    const len = 2000;
    const q = new Vector3(1, 0, 0);
    const half = len / 2;
    const b = physics.world.createRigidBody(
      RAPIER.RigidBodyDesc.fixed()
        .setTranslation(0, Math.sin(ang) * half - Math.cos(ang) * 1, -Math.cos(ang) * half - Math.sin(ang) * 1)
        .setRotation({ x: Math.sin(ang / 2) * q.x, y: 0, z: 0, w: Math.cos(ang / 2) }),
    );
    physics.world.createCollider(RAPIER.ColliderDesc.cuboid(60, 1, half).setCollisionGroups(GROUPS.terrain), b);
    physics.refreshQueries();
    const player = new Player(physics, new Vector3(0, FOOT_OFFSET + WALK.skin + 0.4, -5), UP, FWD);
    const ctl = new AbilityController({ setAbility: () => {}, setWarning: () => {} }, () => 'walk', () => 0);
    ctl.enter({ body: 'mars', power: 'redline' });
    const held = new Set(['KeyQ']);
    const idle: WalkInput = { forward: 0, right: 0, sprint: false, jump: false, yaw: 0, pitch: 0 };
    for (let i = 0; i < 20; i++) {
      player.step(SIM_DT, idle, CENTER, 3.71);
      physics.step();
    }
    let top = 0;
    for (let i = 0; i < 300; i++) {
      const owned = ctl.step(SIM_DT, { player, held: (c) => held.has(c), pressed: () => false, walk: idle, center: CENTER, gravity: 3.71, ready: () => true });
      if (!owned) player.step(SIM_DT, idle, CENTER, 3.71);
      physics.step();
      top = Math.max(top, Math.hypot(player.vel.length(), player.vVert));
    }
    expect(ctl.state).toBe('speed');
    expect(top).toBeGreaterThan((ABILITIES.redline as { params: SpeedParams }).params.top - 2);
    player.dispose();
  });
});
