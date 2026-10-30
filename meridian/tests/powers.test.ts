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
import type { AbilitySave } from '../src/abilities/save';

const UP = new Vector3(0, 1, 0);
const FWD = new Vector3(0, 0, -1);
const CENTER = new Vector3(0, -1e7, 0);

beforeAll(async () => {
  await initPhysics();
});

/**
 * Flat ground (top at y = 0) from z = +400 to -4400 in 400 m tiles: a single
 * box kilometres across lets Rapier's character controller sink the capsule
 * about 0.18 m into it, which real terrain tiles do not.
 */
function groundTiles(physics: Physics): void {
  for (let k = 0; k < 12; k++) {
    const b = physics.world.createRigidBody(RAPIER.RigidBodyDesc.fixed().setTranslation(0, -1, 200 - 400 * k));
    physics.world.createCollider(RAPIER.ColliderDesc.cuboid(200, 1, 200).setCollisionGroups(GROUPS.terrain), b);
  }
}

/** A flat world, a walker and the controller, stepped the way Game steps ON_FOOT. */
function rig(body: string, power: string, gravity: number, opts: { at?: Vector3; restored?: AbilitySave } = {}) {
  const physics = new Physics();
  groundTiles(physics);
  physics.refreshQueries();
  const player = new Player(physics, opts.at ?? new Vector3(0, FOOT_OFFSET + WALK.skin + 0.01, 0), UP, FWD);
  const slots: (AbilitySlot | null)[] = [];
  const warnings: (string | null)[] = [];
  const hud: AbilityHud = { setAbility: (s) => slots.push(s), setWarning: (t) => warnings.push(t) };
  const ctl = new AbilityController(hud, () => 'walk', () => 0);
  ctl.enter({ body, power: power as never, restored: opts.restored ?? null });
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
    // Press and hold Space: the first press jumps (walking), holding on takes
    // off mid-jump at the hold time, without coming down first.
    for (let i = 0; i < 10; i++) r.step();
    expect(r.player.grounded).toBe(true);
    expect(r.height()).toBeCloseTo(WALK.skin, 2); // standing on the ground, not sunk into it
    r.heldKeys.add('Space');
    r.step({ jump: true });
    let tookOff = -1;
    let lowest = Infinity;
    for (let i = 1; i <= 60; i++) {
      r.step();
      if (tookOff < 0 && r.ctl.state === 'flight') tookOff = i;
      if (i > 5) lowest = Math.min(lowest, r.height());
    }
    expect(r.ctl.state).toBe('flight');
    expect(r.ctl.log.at(-1)).toMatchObject({ from: 'walk', to: 'flight' });
    expect(tookOff * SIM_DT).toBeGreaterThan(P.takeoffHold - 2 * SIM_DT);
    expect(tookOff * SIM_DT).toBeLessThan(P.takeoffHold + 2 * SIM_DT);
    expect(lowest).toBeGreaterThan(0.3); // never back on the ground between the jump and the take-off
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

  it('Lunar Step: a click made while not aiming is not kept for later (aiming never steps by itself)', () => {
    const r = rig('moon', 'lunar-step', 1.62);
    for (let i = 0; i < 10; i++) r.step();
    r.player.look(0, -0.07);
    // A stray click (Input latches presses until a step consumes them).
    r.presses.add('MouseLeft');
    for (let i = 0; i < 30; i++) r.step();
    const z0 = r.player.pos.z;
    // Hold right mouse to aim for a second: a preview only, no step.
    r.heldKeys.add('MouseRight');
    for (let i = 0; i < 60; i++) r.step();
    expect(r.player.pos.z).toBeCloseTo(z0, 3);
    expect(r.ctl.view().preview).toMatchObject({ ok: true });
    expect(r.ctl.log).toEqual([]);
    // A fresh click while aiming steps.
    r.presses.add('MouseLeft');
    r.step();
    expect(r.player.pos.z).toBeLessThan(z0 - 15);
    expect(r.ctl.log.map((e) => `${e.from}>${e.to}`)).toEqual(['walk>blink', 'blink>walk']);
    r.player.dispose();
  });
});

describe('save and reload during a power (LEAD M2 plan C)', () => {
  it('a reload mid-flight hovers where it was saved, never falls, and lands only by descending', () => {
    const r = rig('earth', 'skyborne-flight', 9.81);
    const P = (ABILITIES['skyborne-flight'] as { params: FlightParams }).params;
    r.heldKeys.add('Space');
    r.step({ jump: true });
    for (let i = 0; i < 240; i++) r.step();
    r.heldKeys.clear();
    r.heldKeys.add('KeyW');
    for (let i = 0; i < 120; i++) r.step();
    expect(r.ctl.state).toBe('flight');
    const save = JSON.parse(JSON.stringify(r.ctl.snapshot())) as AbilitySave;
    expect(save.abilityState).toBe('flight');
    // Game saves the feet and re-creates the walker there (no velocity is saved).
    const at = r.player.pos.clone();
    const h0 = r.height();
    expect(h0).toBeGreaterThan(40);
    r.player.dispose();
    const q = rig('earth', 'skyborne-flight', 9.81, { at, restored: save });
    expect(q.ctl.state).toBe('flight');
    for (let i = 0; i < 180; i++) q.step();
    expect(q.ctl.state).toBe('flight');
    expect(Math.abs(q.height() - h0)).toBeLessThan(0.05);
    expect(q.player.vel.length() + Math.abs(q.player.vVert)).toBeLessThan(0.01);
    // A reload is not a take-off: no state change logged until it lands.
    expect(q.ctl.log).toEqual([]);
    q.heldKeys.add('ControlLeft');
    let landedAt = -1;
    for (let i = 0; i < 1200 && landedAt < 0; i++) {
      const h = q.height();
      q.step();
      if (q.ctl.state === 'walk') landedAt = h;
    }
    expect(landedAt).toBeGreaterThanOrEqual(0);
    expect(landedAt).toBeLessThan(P.landHeight + 0.2);
    expect(q.ctl.log.map((e) => `${e.from}>${e.to}`)).toEqual(['flight>walk']);
    q.player.dispose();
  });

  it('a reload during superspeed resumes braking and hands back to walking at once, never above sprint speed', () => {
    const r = rig('mars', 'redline', 3.71);
    r.heldKeys.add('KeyQ');
    for (let i = 0; i < 240; i++) r.step();
    expect(r.ctl.state).toBe('speed');
    const save = JSON.parse(JSON.stringify(r.ctl.snapshot())) as AbilitySave;
    expect(save.abilityState).toBe('speed');
    const at = r.player.pos.clone();
    r.player.dispose();
    const q = rig('mars', 'redline', 3.71, { at, restored: save });
    expect(q.ctl.state).toBe('speed');
    let top = 0;
    for (let i = 0; i < 30; i++) {
      q.step();
      top = Math.max(top, q.player.vel.length());
    }
    expect(q.ctl.state).toBe('walk');
    // Braking from rest ends as soon as the re-created walker has found the ground.
    expect(q.states.indexOf('walk')).toBeGreaterThanOrEqual(0);
    expect(q.states.indexOf('walk')).toBeLessThan(3);
    expect(top).toBeLessThanOrEqual(SPEED_EXIT_MAX);
    expect(q.ctl.log.map((e) => `${e.from}>${e.to}`)).toEqual(['speed>walk']);
    q.player.dispose();
  });

  it('a reload with Q still held resumes the run, as releasing and pressing Q again does while braking', () => {
    const q = rig('mars', 'redline', 3.71, { restored: { abilityState: 'speed', unlocked: ['redline'] } });
    q.heldKeys.add('KeyQ');
    for (let i = 0; i < 120; i++) q.step();
    expect(q.ctl.state).toBe('speed');
    expect(q.player.vel.length()).toBeGreaterThan(50);
    q.player.dispose();
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

describe('collision reach for a blink (WORLDS W8 TerrainCollision.reach)', () => {
  it('keeps collision loaded out past the blink range while on foot on a blink body, and only there', async () => {
    const { PlayerRuntime } = await import('../src/player/install');
    const { Group } = await import('three');
    const collision = { reach: 0, readyAt: () => true };
    const game = {
      hud: { setAbility: () => {}, setWarning: () => {} },
      simTime: 0,
      counters: { exits: 0 },
      body: { collision },
      bodyCenterLocal: new Vector3(),
      render: { scene: new Group() },
      player: null,
      audio: {},
    };
    const rt = new PlayerRuntime(game as never);
    const P = (ABILITIES['lunar-step'] as { params: BlinkParams }).params;
    rt.enter({ body: 'moon', power: 'lunar-step' });
    expect(collision.reach).toBeGreaterThan(P.range);
    expect(collision.reach).toBeLessThan(P.range + 20);
    rt.exit('board');
    expect(collision.reach).toBe(0);
    // Flight and superspeed bodies keep WORLDS' default block.
    rt.enter({ body: 'earth', power: 'skyborne-flight' });
    expect(collision.reach).toBe(0);
    rt.exit('board');
    // A collision without the field (before W8) is left untouched.
    const old = { readyAt: () => true } as { readyAt(): boolean; reach?: number };
    const rt2 = new PlayerRuntime({ ...game, body: { collision: old } } as never);
    rt2.enter({ body: 'mars', power: 'redline' });
    rt2.exit('board');
    expect(old.reach).toBeUndefined();
  });
});
