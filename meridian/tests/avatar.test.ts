import { describe, expect, it } from 'vitest';
import { Box3, Group, Vector3, type MeshStandardMaterial } from 'three';
import { buildAvatar, B, BONE_NAMES, DIM, restPosition } from '../src/avatar/AvatarModel';
import { AvatarAnimator, BALL_F, ankleFromBall, footTarget, gaitParams, legIK } from '../src/avatar/AvatarAnimator';
import { Avatar, type AvatarFrame, type GroundRay } from '../src/avatar/Avatar';

const UP = new Vector3(0, 1, 0);
const FWD = new Vector3(0, 0, -1);

/** Drive an Avatar along -Z at a constant speed over flat ground (or a given height profile). */
function walk(avatar: Avatar, speed: number, seconds: number, opts: { dt?: number; heightAt?: (z: number) => number; onFrame?: () => void; feet?: Vector3 } = {}) {
  const dt = opts.dt ?? 1 / 60;
  const steps = Math.round(seconds / dt);
  const feet = opts.feet ?? new Vector3(0, 0, 0);
  const vel = new Vector3(0, 0, -speed);
  let overreach = 0;
  for (let i = 0; i < steps; i++) {
    feet.z -= speed * dt;
    feet.y = opts.heightAt ? opts.heightAt(feet.z) : 0;
    const f: AvatarFrame = { dt, feet: feet.clone(), up: UP, grounded: true, vVert: 0, moveVel: vel, lookHeading: FWD, lookPitch: 0 };
    avatar.update(f);
    overreach = Math.max(overreach, avatar.anim.overreach);
    opts.onFrame?.();
  }
  return { overreach, feet };
}

describe('explorer rig', () => {
  it('has the required bone hierarchy, 1.8 m height and valid skinning', () => {
    const rig = buildAvatar();
    expect(rig.bones.length).toBe(BONE_NAMES.length);
    for (const n of ['hips', 'spine', 'chest', 'head', 'upperArmL', 'lowerArmL', 'handL', 'upperArmR', 'lowerArmR', 'handR', 'upperLegL', 'lowerLegL', 'footL', 'upperLegR', 'lowerLegR', 'footR']) {
      expect(rig.bones.some((b) => b.name === n)).toBe(true);
    }
    // Hierarchy: feet under lower legs under upper legs under hips; hands under forearms under upper arms under chest.
    expect(rig.bones[B.footL].parent).toBe(rig.bones[B.lowerLegL]);
    expect(rig.bones[B.lowerLegL].parent).toBe(rig.bones[B.upperLegL]);
    expect(rig.bones[B.upperLegL].parent).toBe(rig.bones[B.hips]);
    expect(rig.bones[B.handR].parent).toBe(rig.bones[B.lowerArmR]);
    expect(rig.bones[B.upperArmR].parent).toBe(rig.bones[B.chest]);
    expect(rig.bones[B.head].parent).toBe(rig.bones[B.chest]);
    // Bind-pose bounds: feet at 0, top of the helmet at 1.8 m (±3 cm).
    const box = new Box3();
    for (const m of rig.meshes) {
      m.geometry.computeBoundingBox();
      box.union(m.geometry.boundingBox!);
    }
    expect(box.min.y).toBeGreaterThan(-0.01);
    expect(box.min.y).toBeLessThan(0.02);
    expect(box.max.y).toBeGreaterThan(DIM.height - 0.03);
    expect(box.max.y).toBeLessThan(DIM.height + 0.03);
    // Shoulder width reads as a person, not a stick: 0.45–0.65 m.
    expect(box.max.x - box.min.x).toBeGreaterThan(0.45);
    expect(box.max.x - box.min.x).toBeLessThan(0.65);
    // Every vertex is fully weighted to valid bones.
    for (const m of rig.meshes) {
      expect(m.isSkinnedMesh).toBe(true);
      expect(m.skeleton).toBe(rig.skeleton);
      const si = m.geometry.getAttribute('skinIndex');
      const sw = m.geometry.getAttribute('skinWeight');
      for (let i = 0; i < si.count; i++) {
        const w = sw.getX(i) + sw.getY(i) + sw.getZ(i) + sw.getW(i);
        expect(Math.abs(w - 1)).toBeLessThan(1e-5);
        for (const c of [si.getX(i), si.getY(i), si.getZ(i), si.getW(i)]) expect(c).toBeLessThan(rig.bones.length);
      }
      expect((m.material as MeshStandardMaterial).isMeshStandardMaterial).toBe(true);
    }
    // Eye level matches the walker's camera height.
    expect(DIM.eyeY).toBeCloseTo(1.62, 2);
    rig.dispose();
  });

  it('leg IK puts the ankle exactly on its target in 3D (bone forward kinematics)', () => {
    const rig = buildAvatar();
    const hip = restPosition('upperLegL');
    const ankle = new Vector3();
    for (const [f, d, xr] of [[0, 0.8, 0], [0.3, 0.75, 0.02], [-0.35, 0.7, -0.05], [0.1, 0.5, 0.12], [-0.6, 0.55, 0.03]]) {
      const ik = legIK(f, d, xr);
      expect(ik.knee).toBeLessThanOrEqual(0); // knees never bend backward
      rig.bones[B.upperLegL].rotation.set(ik.hip, 0, ik.abd);
      rig.bones[B.lowerLegL].rotation.set(ik.knee, 0, 0);
      rig.root.updateMatrixWorld(true);
      rig.bones[B.footL].getWorldPosition(ankle);
      // Model frame: forward = -Z, right = +X.
      expect(-(ankle.z - hip.z)).toBeCloseTo(f, 4);
      expect(hip.y - ankle.y).toBeCloseTo(d, 4);
      expect(ankle.x - hip.x).toBeCloseTo(xr, 4);
    }
    rig.dispose();
  });

  it('stance foot targets move backward exactly as far as the body travels', () => {
    for (const v of [1.2, 4.5, 7.5]) {
      const g = gaitParams(v);
      const a = footTarget(0, g);
      const b = footTarget(g.stance * 0.6, g);
      // Moving 0.6 of the stance means travelling 0.6 * stance * cycle metres: the foot target moves back the same.
      expect(a.f - b.f).toBeCloseTo(g.stance * g.cycle * 0.6, 6);
      expect(a.stance && b.stance).toBe(true);
      // Contact stays within what a 0.85 m leg can reach with a heel roll.
      expect(g.span).toBeLessThanOrEqual(1.0);
      expect(g.front).toBeLessThanOrEqual(0.36);
    }
    // Cadence stays human: about 0.9–1.6 cycles per second from a walk to a sprint.
    for (const [v, lo, hi] of [[1.4, 0.8, 1.1], [4.5, 1.2, 1.45], [7.5, 1.45, 1.65]]) expect(v / gaitParams(v).cycle).toBeGreaterThan(lo), expect(v / gaitParams(v).cycle).toBeLessThan(hi);
  });

  it('a foot rolled over its ball keeps the ball in place', () => {
    const flat = ankleFromBall(0.2, 0, 0);
    expect(flat.f).toBeCloseTo(0.2 - BALL_F, 6);
    expect(flat.y).toBeCloseTo(0, 6);
    const rolled = ankleFromBall(0.2, 0, -0.8);
    // Heel up: the ankle rises and moves toward the ball, the ball stays at f = 0.2.
    expect(rolled.y).toBeGreaterThan(0.05);
    expect(rolled.f).toBeGreaterThan(flat.f);
    expect(Math.hypot(rolled.f - 0.2, rolled.y + DIM.ankleY)).toBeCloseTo(Math.hypot(BALL_F, DIM.ankleY), 6);
  });
});

describe('explorer animation', () => {
  it('plants feet without sliding at walk, jog and sprint speeds on flat ground', () => {
    for (const speed of [1.5, 4.5, 7.5]) {
      const parent = new Group();
      const av = new Avatar(parent, null, FWD);
      const { overreach } = walk(av, speed, 6);
      expect(av.slipSamples).toBeGreaterThan(50);
      expect(av.maxSlip).toBeLessThan(0.002); // < 2 mm: planted feet are locked
      expect(overreach).toBe(0);
      expect(av.anim.state).toBe(speed > 6 ? 'run' : 'walk');
      av.dispose();
      expect(parent.children.length).toBe(0);
    }
  });

  it('keeps the same gait at 30, 60 and 144 frames per second (distance-driven)', () => {
    const rates: number[] = [];
    for (const fps of [30, 60, 144]) {
      const av = new Avatar(new Group(), null, FWD);
      const feet = new Vector3();
      walk(av, 4.5, 3, { dt: 1 / fps, feet });
      // Steady state: phase advance over one more second.
      const p0 = av.anim.phase;
      walk(av, 4.5, 1, { dt: 1 / fps, feet });
      rates.push((av.anim.phase - p0 + 1) % 1);
      expect(av.maxSlip).toBeLessThan(0.01);
      expect(av.anim.state).toBe('walk');
      av.dispose();
    }
    expect(Math.abs(rates[0] - rates[2])).toBeLessThan(1e-3);
    expect(Math.abs(rates[1] - rates[2])).toBeLessThan(1e-3);
  });

  it('adapts feet to a 25° slope without sinking or overreaching', () => {
    const slope = Math.tan((25 * Math.PI) / 180);
    const heightAt = (z: number) => -z * slope + 0.35 * (1 / Math.cos(Math.atan(slope)) - 1); // capsule axis floats above a slope
    const plane = (p: Vector3) => p.y - -p.z * slope; // height of a point above the ground plane
    const ray: GroundRay = (o, d, max) => {
      // Ray along -Y against the plane y = -z * slope.
      const h = plane(o);
      if (h < 0 || h > max) return null;
      const n = new Vector3(0, 1, slope).normalize();
      return { dist: h / -d.y, normal: n };
    };
    const av = new Avatar(new Group(), ray, FWD);
    // Ankles stay above the slope: never lower than the rest ankle height minus 2 cm.
    let lowest = Infinity;
    const p = new Vector3();
    const cos = Math.cos(Math.atan(slope));
    const { overreach } = walk(av, 3, 5, {
      heightAt,
      onFrame: () => {
        for (const b of [B.footL, B.footR]) {
          av.rig.bones[b].getWorldPosition(p);
          lowest = Math.min(lowest, plane(p) * cos);
        }
      },
    });
    expect(overreach).toBe(0);
    expect(av.slipSamples).toBeGreaterThan(30);
    expect(av.maxSlip).toBeLessThan(0.015);
    expect(lowest).toBeGreaterThan(DIM.ankleY - 0.02);
    av.dispose();
  });

  it('runs the idle → walk → run → jump → fall → land → idle sequence', () => {
    const an = new AvatarAnimator();
    const dt = 1 / 60;
    const run = (s: number, v: number, grounded: boolean, vVert: number) => {
      for (let t = 0; t < s; t += dt) an.update({ dt, forwardDist: v * dt, grounded, vVert });
    };
    run(0.5, 0, true, 0);
    expect(an.state).toBe('idle');
    run(1.5, 3, true, 0);
    expect(an.state).toBe('walk');
    run(1.5, 7.5, true, 0);
    expect(an.state).toBe('run');
    run(0.3, 7.5, false, 4);
    expect(an.state).toBe('jump');
    run(0.5, 7.5, false, -5);
    expect(an.state).toBe('fall');
    an.update({ dt, forwardDist: 0, grounded: true, vVert: 0 });
    expect(an.state).toBe('land');
    run(1.0, 0, true, 0);
    expect(an.state).toBe('idle');
    for (const s of ['idle', 'walk', 'run', 'jump', 'fall', 'land'] as const) expect(an.entries[s]).toBeGreaterThanOrEqual(1);
    // A short hop off a bump (< 0.12 s, falling) keeps the walking gait.
    const b = new AvatarAnimator();
    for (let t = 0; t < 1; t += dt) b.update({ dt, forwardDist: 3 * dt, grounded: true, vVert: 0 });
    for (let t = 0; t < 0.08; t += dt) b.update({ dt, forwardDist: 3 * dt, grounded: false, vVert: -1 });
    expect(b.state).toBe('walk');
  });

  it('stands still without shuffling and stops with at most one settle step per foot', () => {
    const av = new Avatar(new Group(), null, FWD);
    const feet = new Vector3();
    const run = (v: number, s: number) => {
      for (let t = 0; t < s; t += 1 / 60) {
        feet.z -= v / 60;
        av.update({ dt: 1 / 60, feet: feet.clone(), up: UP, grounded: true, vVert: 0, moveVel: new Vector3(0, 0, -v), lookHeading: FWD, lookPitch: 0 });
      }
    };
    run(0, 2);
    expect(av.anim.settleSteps).toBe(0);
    run(4.5, 3);
    run(0, 2);
    expect(av.anim.settleSteps).toBeLessThanOrEqual(2);
    expect(av.anim.state).toBe('idle');
    const n = av.anim.settleSteps;
    run(0, 3);
    expect(av.anim.settleSteps).toBe(n);
    expect(av.maxSlip).toBeLessThan(0.002);
    av.dispose();
  });

  it('freezes when paused (dt = 0)', () => {
    const an = new AvatarAnimator();
    for (let i = 0; i < 60; i++) an.update({ dt: 1 / 60, forwardDist: 0.07, grounded: true, vVert: 0 });
    const before = an.rot.slice();
    const phase = an.phase;
    for (let i = 0; i < 60; i++) an.update({ dt: 0, forwardDist: 0.07, grounded: true, vVert: 0 });
    expect(an.phase).toBe(phase);
    expect(Array.from(an.rot)).toEqual(Array.from(before));
  });

  it('turns toward the movement direction and ignores teleports for the gait', () => {
    const av = new Avatar(new Group(), null, FWD);
    const dt = 1 / 60;
    const feet = new Vector3();
    const side = new Vector3(1, 0, 0);
    for (let i = 0; i < 30; i++) {
      feet.x += 3 * dt;
      av.update({ dt, feet: feet.clone(), up: UP, grounded: true, vVert: 0, moveVel: side.clone().multiplyScalar(3), lookHeading: FWD, lookPitch: 0 });
    }
    expect(av.facing.dot(side)).toBeGreaterThan(0.99);
    const phase = av.anim.phase;
    feet.x += 500; // placement (recovery), not a step
    av.update({ dt, feet: feet.clone(), up: UP, grounded: true, vVert: 0, moveVel: new Vector3(), lookHeading: FWD, lookPitch: 0 });
    expect(Math.abs(av.anim.phase - phase)).toBeLessThan(0.05);
    av.dispose();
  });
});
