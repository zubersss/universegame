import { beforeAll, describe, expect, it } from 'vitest';
import { Group, Mesh, PerspectiveCamera, Vector3 } from 'three';
import { PlayerRuntime } from '../src/player/install';
import { BlinkPower } from '../src/abilities/powers';
import type { PowerVfx } from '../src/abilities/vfx';
import { ABILITIES } from '../src/abilities/catalog';
import type { SpeedParams } from '../src/abilities/types';
import { BODIES } from '../src/world/bodies';
import { initPhysics, Physics, RAPIER, GROUPS } from '../src/physics/Physics';
import { Player, FOOT_OFFSET, type WalkInput } from '../src/player/Player';
import { CameraRig } from '../src/render/CameraRig';
import { SIM_DT, WALK } from '../src/game/config';

// PlayerRuntime (the ON_FOOT hooks) driven the way Game drives it, with a
// stand-in Game: real physics, walker, explorer and camera; Input that
// latches presses until a step consumes them; a ship transform for the ladder.

const UP = new Vector3(0, 1, 0);
const FWD = new Vector3(0, 0, -1);
const IDLE: WalkInput = { forward: 0, right: 0, sprint: false, jump: false, yaw: 0, pitch: 0 };

beforeAll(async () => {
  await initPhysics();
});

function game(bodyId: 'mars' | 'moon' | 'earth', power: string, gravity: number) {
  const physics = new Physics();
  for (let k = 0; k < 6; k++) {
    const b = physics.world.createRigidBody(RAPIER.RigidBodyDesc.fixed().setTranslation(0, -1, 200 - 400 * k));
    physics.world.createCollider(RAPIER.ColliderDesc.cuboid(200, 1, 200).setCollisionGroups(GROUPS.terrain), b);
  }
  physics.refreshQueries();
  const def = BODIES[bodyId];
  const R = def.radius;
  const center = new Vector3(0, -R, 0);
  const player = new Player(physics, new Vector3(0, FOOT_OFFSET + WALK.skin + 0.01, 0), UP, FWD);
  const held = new Set<string>();
  const pressed = new Set<string>();
  const warnings: (string | null)[] = [];
  let target: { kind: string } | null = null;
  // As in Game: the camera rig moves the render camera.
  const camera = new PerspectiveCamera();
  const g = {
    hud: { setAbility: () => {}, setWarning: (t: string | null) => warnings.push(t) },
    simTime: 0,
    counters: { exits: 0 },
    ship: { localToWorld: (v: Vector3, out: Vector3) => out.copy(v).add(new Vector3(4, 0, 4)) },
    physics,
    bodyCenterLocal: center,
    // System position of the walker = local + origin; the body's centre sits R below it.
    origin: new Vector3(def.center[0], def.center[1] + R, def.center[2]),
    body: { def, collision: { readyAt: () => true, reach: 0 } },
    input: { isDown: (c: string) => held.has(c), consume: (c: string) => pressed.delete(c), press: (c: string) => void pressed.add(c) },
    player,
    render: { scene: new Group(), camera },
    lighting: { envMap: null },
    settings: { reducedMotion: false },
    cameraRig: new CameraRig(camera),
    audio: {},
    interactionTarget: () => target,
  };
  const rt = new PlayerRuntime(g as never);
  rt.enter({ body: bodyId, power: power as never });
  /** One fixed step as Game.stepOnFoot runs it, then one rendered frame at the end of it (alpha null: no frame). */
  const step = (walk: Partial<WalkInput> = {}, alpha: number | null = 1) => {
    const w = { ...IDLE, ...walk };
    if (!rt.step(SIM_DT, w)) player.step(SIM_DT, w, center, gravity);
    physics.step();
    g.simTime += SIM_DT;
    if (alpha !== null) rt.frame(SIM_DT, alpha);
  };
  return { rt, g, player, held, pressed, warnings, step, atShip: (on: boolean) => (target = on ? { kind: 'ship' } : null) };
}

describe('PlayerRuntime with a stand-in Game', () => {
  it('E at the ship under superspeed does not board or freeze the runner: it says brake first and the braking goes on', () => {
    const h = game('mars', 'redline', 3.71);
    const P = (ABILITIES.redline as { params: SpeedParams }).params;
    for (let i = 0; i < 10; i++) h.step();
    h.held.add('KeyQ');
    for (let i = 0; i < 60; i++) h.step();
    expect(h.rt.abilities.state).toBe('speed');
    h.held.delete('KeyQ'); // braking
    h.atShip(true);
    h.pressed.add('KeyE');
    h.step();
    let prev = h.player.vel.length();
    expect(h.rt.transition).toBeNull(); // no ladder climb out of a power
    expect(h.pressed.has('KeyE')).toBe(false); // used up: Game cannot board from superspeed either
    expect(h.warnings.at(-1)).toBe('Redline: brake first');
    // It keeps braking at the brake rate down to walking.
    let walkAt = -1;
    for (let i = 0; i < 240 && walkAt < 0; i++) {
      h.step();
      const v = h.player.vel.length();
      expect(prev - v).toBeLessThanOrEqual(P.brake * SIM_DT + 0.05);
      prev = v;
      if (h.rt.abilities.state === 'walk') walkAt = i;
    }
    expect(walkAt).toBeGreaterThan(0);
    // Walking now: E at the ship starts the ladder climb.
    for (let i = 0; i < 30; i++) h.step();
    h.pressed.add('KeyE');
    h.step();
    expect(h.rt.transition?.kind).toBe('board');
    h.player.dispose();
  });

  it('speed lines are centred where the body is drawn between steps, not on the newest step ahead of it', () => {
    const h = game('mars', 'redline', 3.71);
    for (let i = 0; i < 10; i++) h.step();
    h.held.add('KeyQ');
    for (let i = 0; i < 150; i++) h.step();
    expect(h.player.vel.length()).toBeGreaterThan(40);
    const vfx = (h.rt as unknown as { vfx: PowerVfx }).vfx;
    let center: Vector3 | null = null;
    const update = vfx.update.bind(vfx);
    vfx.update = (dt, f, reduced) => {
      center = f.rush ? f.rush.center.clone() : null;
      update(dt, f, reduced);
    };
    // A frame halfway between two steps (a 120 Hz display).
    h.step({}, null);
    h.rt.frame(SIM_DT / 2, 0.5);
    const drawn = new Vector3().lerpVectors(h.player.prevPos, h.player.pos, 0.5);
    expect(center).not.toBeNull();
    expect(center!.distanceTo(drawn)).toBeLessThan(1e-9);
    expect(h.player.pos.distanceTo(drawn)).toBeGreaterThan(0.3);
    h.player.dispose();
  });

  it('while flying, leaving the page asks first (Ctrl+W is descend + faster); walking and after exit it does not', () => {
    const listeners = new Set<(e: { preventDefault(): void; returnValue: string }) => void>();
    const g = globalThis as unknown as { window?: unknown };
    const had = 'window' in g;
    g.window = {
      addEventListener: (type: string, fn: never) => type === 'beforeunload' && listeners.add(fn),
      removeEventListener: (type: string, fn: never) => type === 'beforeunload' && listeners.delete(fn),
    };
    try {
      const h = game('earth', 'skyborne-flight', 9.81);
      for (let i = 0; i < 10; i++) h.step();
      expect(listeners.size).toBe(0);
      h.held.add('Space');
      h.step({ jump: true });
      for (let i = 0; i < 60 && h.rt.abilities.state !== 'flight'; i++) h.step();
      expect(h.rt.abilities.state).toBe('flight');
      expect(listeners.size).toBe(1);
      let prevented = false;
      const e = { preventDefault: () => void (prevented = true), returnValue: 'x' };
      for (const fn of listeners) fn(e);
      expect(prevented).toBe(true);
      h.rt.exit('board');
      expect(listeners.size).toBe(0);
      h.player.dispose();
    } finally {
      if (!had) delete g.window;
    }
  });

  it('presses made on the exit ladder are not kept for later: no blink, no early E when the climb ends', () => {
    const h = game('moon', 'lunar-step', 1.62);
    for (let i = 0; i < 5; i++) h.step();
    h.g.counters.exits = 1; // a fresh exit: the runtime climbs down the ladder
    h.step();
    const t = h.rt.transition;
    expect(t?.kind).toBe('exit');
    h.player.look(0, -0.07); // looking at ground ~23 m ahead
    let steps = 0;
    while (h.rt.transition && steps < 1200) {
      if (steps === 20) {
        h.pressed.add('KeyQ');
        h.pressed.add('KeyE');
      }
      h.step();
      steps++;
    }
    expect(h.rt.transition).toBeNull();
    for (let i = 0; i < 60; i++) h.step();
    expect(h.rt.abilities.log).toEqual([]); // the Q from the ladder never fired a blink
    expect(h.pressed.size).toBe(0);
    h.player.dispose();
  });

  it('a floating-origin rebase moves the last blink and its flashes with the walker', () => {
    const h = game('moon', 'lunar-step', 1.62);
    for (let i = 0; i < 10; i++) h.step();
    h.player.look(0, -0.07);
    h.pressed.add('KeyQ');
    h.step();
    const rt = h.rt.abilities.runtime as BlinkPower;
    expect(rt.lastJump.count).toBe(1);
    const to = rt.lastJump.to.clone();
    const vfx = (h.rt as unknown as { vfx: { root: Group } }).vfx;
    const flashes = () => vfx.root.children.filter((o) => (o as Mesh).isMesh && o.visible && (o as Mesh).geometry.type === 'SphereGeometry').map((o) => o.position.clone());
    const before = flashes();
    expect(before.length).toBe(2);
    const d = new Vector3(-2048, 0, 1024);
    h.player.onRebase(d);
    expect(rt.lastJump.to.distanceTo(to.clone().add(d))).toBeLessThan(1e-9);
    const after = flashes();
    for (let i = 0; i < 2; i++) expect(after[i].distanceTo(before[i].clone().add(d))).toBeLessThan(1e-9);
    // Exit unhooks the runtime from the walker.
    h.rt.exit('board');
    expect(h.player.onRebaseHook).toBeNull();
    h.player.dispose();
  });

  it('a short blink is a placement: the explorer stands still on arrival instead of running in place', () => {
    const h = game('moon', 'lunar-step', 1.62);
    for (let i = 0; i < 30; i++) h.step();
    h.player.look(0, -0.55); // ground about 2.7 m ahead
    h.step(); // the aim follows the camera, which takes the new look on the next frame
    h.step();
    const z0 = h.player.pos.z;
    h.pressed.add('KeyQ');
    h.step();
    const moved = z0 - h.player.pos.z;
    expect(moved).toBeGreaterThan(1.5);
    expect(moved).toBeLessThan(3); // under the 3 m placement heuristic
    const states = new Set<string>();
    for (let i = 0; i < 30; i++) {
      h.step();
      states.add(h.player.avatar!.anim.state);
    }
    expect(states.has('run')).toBe(false);
    expect(states.has('walk')).toBe(false);
    expect(h.player.avatar!.anim.speed).toBeLessThan(0.3);
    h.player.dispose();
  });
});
