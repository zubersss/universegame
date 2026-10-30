import { beforeAll, describe, expect, it } from 'vitest';
import { Group, Mesh, PerspectiveCamera, Vector3 } from 'three';
import { AbilityController } from '../src/abilities/AbilityController';
import { BlinkPower, type PowerWorld } from '../src/abilities/powers';
import { ABILITIES } from '../src/abilities/catalog';
import { PowerVfx, rushStrength, trailStrength, type VfxFrame } from '../src/abilities/vfx';
import type { FlightParams } from '../src/abilities/types';
import { initPhysics, Physics, RAPIER, GROUPS } from '../src/physics/Physics';
import { Player, FOOT_OFFSET, type WalkInput } from '../src/player/Player';
import { CHAR_CAMERA } from '../src/player/CharacterCamera';
import { CameraRig } from '../src/render/CameraRig';
import { CAMERA, SIM_DT, WALK } from '../src/game/config';

// Charter K: every power is tested at a low frame rate. Game runs fixed
// 60 Hz steps and renders once per frame, so at 30, 20 or 15 fps a frame
// samples the controls once, runs 2, 3 or 4 steps (a latched press is seen by
// the first step that reads it), then renders the explorer, the character
// camera and the effects with the long frame time. The outcome must match
// 60 fps and the rendered side must stay sane.

const UP = new Vector3(0, 1, 0);
const FWD = new Vector3(0, 0, -1);
const CENTER = new Vector3(0, -1e7, 0);
const IDLE: WalkInput = { forward: 0, right: 0, sprint: false, jump: false, yaw: 0, pitch: 0 };
const RATES = [60, 30, 20, 15];

beforeAll(async () => {
  await initPhysics();
});

/** Controls by simulation time: held keys, presses made this frame, look. Boundaries sit on multiples of 1/15 s, a frame start at every rate. */
type Script = (t: number) => { held?: string[]; press?: string[]; jump?: boolean; pitch?: number };

interface FrameSample {
  t: number;
  state: string;
  avatar: string;
  camera: Vector3;
  eye: Vector3;
  fov: number;
  streaks: number;
  trails: number;
  marker: boolean;
}

/** A fresh script per run (scripts may keep one-shot presses in a closure). */
function play(body: string, power: string, gravity: number, fps: number, seconds: number, makeScript: () => Script) {
  const script = makeScript();
  const physics = new Physics();
  const ground = physics.world.createRigidBody(RAPIER.RigidBodyDesc.fixed().setTranslation(0, -1, -700));
  physics.world.createCollider(RAPIER.ColliderDesc.cuboid(900, 1, 900).setCollisionGroups(GROUPS.terrain), ground);
  physics.refreshQueries();
  const player = new Player(physics, new Vector3(0, FOOT_OFFSET + WALK.skin + 0.01, 0), UP, FWD);
  const scene = new Group();
  player.attachVisual(scene);
  const rig = new CameraRig(new PerspectiveCamera(CAMERA.fov, 16 / 9, 0.05, 5000));
  let simTime = 0;
  const ctl = new AbilityController({ setAbility: () => {}, setWarning: () => {} }, () => 'walk', () => simTime);
  ctl.enter({ body, power: power as never });
  const vfx = new PowerVfx(scene, '#c8b6ff');
  const streakMeshes: Mesh[] = [];
  const trailMeshes: Mesh[] = [];
  vfx.root.traverse((o) => {
    const m = o as Mesh;
    if (!m.isMesh || m.parent !== vfx.root) return;
    const g = m.geometry as unknown as { parameters?: { height?: number }; getAttribute(n: string): unknown };
    if (g.parameters?.height === 3.2) streakMeshes.push(m);
    else if (g.getAttribute('color')) trailMeshes.push(m);
  });
  const held = new Set<string>();
  const presses = new Set<string>();
  let pitch = 0;
  const per = Math.round(60 / fps);
  const steps: { t: number; state: string; pos: Vector3; speed: number }[] = [];
  const frames: FrameSample[] = [];
  let blinks = 0;
  const tips = [new Vector3(), new Vector3()] as const;
  for (let f = 0; f < Math.round(seconds * fps); f++) {
    // Sampled just past the frame start: simTime sums float steps, and a
    // boundary must not slip by a frame (a different number of steps per rate).
    const s = script(simTime + 1e-6);
    held.clear();
    for (const k of s.held ?? []) held.add(k);
    for (const k of s.press ?? []) presses.add(k);
    if (s.pitch !== undefined) pitch = s.pitch;
    for (let k = 0; k < per; k++) {
      // Look is absolute here (no mouse delta), so every step sees the same pitch.
      const walk: WalkInput = { ...IDLE, jump: k === 0 && !!s.jump, yaw: 0, pitch: pitch - player.pitch };
      const world: PowerWorld = { player, held: (c) => held.has(c), pressed: (c) => presses.delete(c), walk, center: CENTER, gravity, ready: () => true };
      const owned = ctl.step(SIM_DT, world);
      if (!owned) player.step(SIM_DT, walk, CENTER, gravity);
      physics.step();
      simTime += SIM_DT;
      steps.push({ t: simTime, state: ctl.state, pos: player.pos.clone(), speed: Math.hypot(player.vel.length(), player.vVert) });
    }
    // Render once per frame, as PlayerRuntime.frame does.
    const dt = 1 / fps;
    const motion = ctl.motion();
    player.renderView(dt, 1, rig, false, null, motion);
    const rt = ctl.runtime;
    let aim: VfxFrame['aim'] = null;
    if (rt instanceof BlinkPower) {
      if (rt.aiming) aim = { feet: rt.target.feet, ok: rt.target.ok };
      if (rt.lastJump.count !== blinks) {
        blinks = rt.lastJump.count;
        vfx.flash(rt.lastJump.to.clone().addScaledVector(UP, 1));
      }
    }
    let rush: VfxFrame['rush'] = null;
    let trails: VfxFrame['trails'] = null;
    if (motion) {
      const dir = player.vel.clone().addScaledVector(UP, motion.mode === 'flight' ? player.vVert : 0);
      if (dir.lengthSq() > 1) {
        dir.normalize();
        rush = { center: player.pos, dir, speed: motion.speed, strength: rushStrength(motion.mode, motion.speed) };
        if (motion.mode === 'flight' && trailStrength(motion.speed) > 0) {
          player.avatar!.bootTips(tips[0], tips[1]);
          trails = { from: tips, dir, strength: trailStrength(motion.speed) };
        }
      }
    }
    vfx.update(dt, { up: UP, camera: rig.camera.position, aim, rush, trails }, false);
    frames.push({
      t: simTime,
      state: ctl.state,
      avatar: player.avatar!.state,
      camera: rig.camera.position.clone(),
      eye: player.eye(1, new Vector3()),
      fov: rig.camera.fov,
      streaks: streakMeshes.filter((m) => m.visible).length,
      trails: trailMeshes.filter((m) => m.visible).length,
      marker: !!aim,
    });
  }
  const result = { steps, frames, log: ctl.log.map((e) => ({ ...e })), avatar: player.avatar!, player };
  vfx.dispose();
  player.dispose();
  return result;
}

/** Every rendered frame: a finite camera above the ground, outside the body, with the field of view in bounds. */
function expectSaneFrames(frames: FrameSample[]): void {
  for (const f of frames) {
    expect([f.camera.x, f.camera.y, f.camera.z, f.fov].every(Number.isFinite)).toBe(true);
    expect(f.camera.y).toBeGreaterThan(0.1);
    expect(f.fov).toBeGreaterThanOrEqual(CAMERA.fov - 1e-6);
    expect(f.fov).toBeLessThanOrEqual(CAMERA.fov + CHAR_CAMERA.fovMaxExtra + 1e-6);
  }
}

const firstTime = (steps: { t: number; state: string }[], state: string, after = 0) => steps.find((s) => s.t > after && s.state === state)?.t ?? -1;

describe('powers at low frame rates (fixed steps, one render per frame)', () => {
  it('Skyborne Flight: same take-off, cruise, boost, hover and landing at 60, 30, 20 and 15 fps', () => {
    const P = (ABILITIES['skyborne-flight'] as { params: FlightParams }).params;
    // Hold Space (the first frame jumps), climb, cruise, boost, hover, descend.
    const script = (): Script => (t) => {
      if (t < 1) return { held: ['Space'], jump: t < 0.001 };
      if (t < 3) return { held: ['Space'] };
      if (t < 6) return { held: ['KeyW'] };
      if (t < 12) return { held: ['KeyW', 'ShiftLeft'] };
      if (t < 16) return { held: ['KeyX'] };
      return { held: ['ControlLeft'] };
    };
    const runs = RATES.map((fps) => ({ fps, ...play('earth', 'skyborne-flight', 9.81, fps, 30, script) }));
    const base = runs[0];
    const takeoff = firstTime(base.steps, 'flight');
    const landing = firstTime(base.steps, 'walk', takeoff);
    expect(takeoff).toBeGreaterThan(0.55);
    expect(landing).toBeGreaterThan(16);
    for (const r of runs) {
      expect(r.log.map((e) => `${e.from}>${e.to}`), `${r.fps} fps`).toEqual(['walk>flight', 'flight>walk']);
      // Inputs change on frame boundaries common to all rates, so the fixed steps match exactly.
      expect(Math.abs(firstTime(r.steps, 'flight') - takeoff)).toBeLessThan(1e-9);
      expect(Math.abs(firstTime(r.steps, 'walk', takeoff) - landing)).toBeLessThan(1e-9);
      expect(r.steps.at(-1)!.pos.distanceTo(base.steps.at(-1)!.pos)).toBeLessThan(1e-6);
      // Boost reached its speed, the landing was low and slow.
      expect(Math.max(...r.steps.map((s) => s.speed))).toBeGreaterThan(P.boost * 0.9);
      const landed = r.steps.find((s) => s.t === landing)!;
      expect(landed.pos.y - FOOT_OFFSET).toBeLessThan(P.landHeight + 0.2);
      // The rendered side: sane camera every frame, the flying pose in the air,
      // trails only while boosting, the explorer standing again at the end.
      expectSaneFrames(r.frames);
      const boosting = r.frames.filter((f) => f.t > 10 && f.t < 12);
      expect(boosting.length).toBeGreaterThan(20);
      expect(boosting.every((f) => f.avatar === 'fly' && f.trails === 2 && f.streaks > 0)).toBe(true);
      const cruising = r.frames.filter((f) => f.t > 1.5 && f.t < 5);
      expect(cruising.length).toBeGreaterThan(40);
      expect(cruising.every((f) => f.avatar === 'fly' && f.trails === 0)).toBe(true);
      // The camera stays out of the body (the arm only shortens against geometry; there is none up here).
      const flying = r.frames.filter((f) => f.state === 'flight' && f.t > 2);
      expect(flying.length).toBeGreaterThan(14 * r.fps);
      for (const f of flying) expect(f.camera.distanceTo(f.eye)).toBeGreaterThan(CHAR_CAMERA.flightArm - 1);
      expect(['idle', 'land']).toContain(r.frames.at(-1)!.avatar);
      expect(r.frames.at(-1)!.fov).toBeLessThan(CAMERA.fov + 0.5);
    }
  });

  it('Redline: same run and braking hand-back at 60, 30, 20 and 15 fps; the feet do not slide once walking', () => {
    const script = (): Script => (t) => (t < 3 ? { held: ['KeyQ'] } : {});
    const runs = RATES.map((fps) => ({ fps, ...play('mars', 'redline', 3.71, fps, 8, script) }));
    const base = runs[0];
    const handBack = firstTime(base.steps, 'walk', firstTime(base.steps, 'speed'));
    expect(handBack).toBeGreaterThan(4.5);
    for (const r of runs) {
      expect(r.log.map((e) => `${e.from}>${e.to}`), `${r.fps} fps`).toEqual(['walk>speed', 'speed>walk']);
      expect(Math.abs(firstTime(r.steps, 'walk', firstTime(r.steps, 'speed')) - handBack)).toBeLessThan(1e-9);
      expect(r.steps.at(-1)!.pos.distanceTo(base.steps.at(-1)!.pos)).toBeLessThan(1e-6);
      expect(Math.max(...r.steps.map((s) => s.speed))).toBeGreaterThan(100);
      expectSaneFrames(r.frames);
      const running = r.frames.filter((f) => f.t > 2.5 && f.t < 3);
      expect(running.length).toBeGreaterThan(6);
      expect(running.every((f) => f.avatar === 'dash' && f.streaks > 0 && f.trails === 0)).toBe(true);
      // Back to walking: the explorer comes to rest without sliding its planted feet.
      expect(r.avatar.maxSlip).toBeLessThan(0.02);
      expect(r.frames.at(-1)!.avatar).toBe('idle');
    }
  });

  it('Lunar Step: the aimed step lands on the same spot at 60, 30, 20 and 15 fps, and the marker shows while aiming', () => {
    // Look 4 degrees down, hold right mouse to aim, click once to step; click again during the cooldown.
    const script = (): Script => {
      let clicks = 0;
      return (t) => {
        if (t < 0.4) return { pitch: -0.07 };
        if (t < 1.4) return { held: ['MouseRight'] };
        if (clicks === 0) return clicks++, { held: ['MouseRight'], press: ['MouseLeft'] };
        if (t < 2) return { held: ['MouseRight'] };
        if (clicks === 1) return clicks++, { held: ['MouseRight'], press: ['MouseLeft'] };
        if (t < 2.4) return { held: ['MouseRight'] };
        return {};
      };
    };
    const runs = RATES.map((fps) => ({ fps, ...play('moon', 'lunar-step', 1.62, fps, 3, script) }));
    const arrival = (r: (typeof runs)[number]) => {
      const i = r.steps.findIndex((s) => s.t > 1.4 && r.steps[0].pos.distanceTo(s.pos) > 10);
      expect(r.steps[i].t).toBeCloseTo(1.4 + 1 / 60, 6); // the click's own step
      return r.steps[i].pos;
    };
    const base = arrival(runs[0]);
    expect(runs[0].steps[0].pos.distanceTo(base)).toBeGreaterThan(15);
    for (const r of runs) {
      // One step: the second click came during the cooldown.
      expect(r.log.map((e) => `${e.from}>${e.to}`), `${r.fps} fps`).toEqual(['walk>blink', 'blink>walk']);
      expect(arrival(r).distanceTo(base)).toBeLessThan(0.02);
      expectSaneFrames(r.frames);
      const aiming = r.frames.filter((f) => f.t > 0.6 && f.t < 1.4);
      expect(aiming.length).toBeGreaterThan(10);
      expect(aiming.every((f) => f.marker)).toBe(true);
      expect(r.frames.filter((f) => f.t > 2.5).some((f) => f.marker)).toBe(false);
    }
  });
});
