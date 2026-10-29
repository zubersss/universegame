import type { Bone } from 'three';
import { B, BONE_NAMES, DIM } from './AvatarModel';

// Procedural, state-blended animation for the explorer. Ground locomotion is a
// gait whose phase advances with the distance actually travelled, and whose
// stance foot target moves backward exactly as fast as the body moves forward,
// so a planted foot stays put (no foot sliding). Legs are solved with
// analytic two-bone IK in the sagittal plane. Air and landing poses blend in
// on top. Everything is a pure function of the inputs and the clock.

export type AnimState = 'idle' | 'walk' | 'run' | 'jump' | 'fall' | 'land';

export interface AnimInput {
  /** Frame time (s); 0 freezes the animation (pause). */
  dt: number;
  /** Signed distance moved along the facing direction this frame (m). */
  forwardDist: number;
  grounded: boolean;
  /** Vertical speed along up (m/s). */
  vVert: number;
}

const N = BONE_NAMES.length;
const LEG = DIM.thigh + DIM.shin;
const REACH = LEG * 0.995;
/** Hip joint height above the ankle in the rest pose. */
const HIP_ABOVE_ANKLE = DIM.hipY - 0.02 - DIM.ankleY;

/** Gait parameters for a ground speed (m/s): cycle length, stance fraction, lift, crouch. */
export function gaitParams(v: number): { cycle: number; stance: number; lift: number; crouch: number; run: number } {
  const run = smooth(3.2, 6.2, v);
  return {
    // Cycle length (two steps) grows with speed: ~1.4 m at 1.5 m/s, ~2.4 m at 4.5 m/s, ~3.3 m at 7.5 m/s.
    cycle: clampN(0.95 + 0.31 * v, 1.1, 3.4),
    // Walking keeps a foot down ~60% of the cycle; running ~34% (with a flight phase).
    stance: 0.6 - 0.26 * run,
    lift: 0.1 + 0.14 * run,
    crouch: 0.02 + 0.03 * smooth(0.2, 2, v) + 0.035 * run,
    run,
  };
}

/**
 * Foot target relative to the point under the hip for leg phase p in [0,1):
 * f = forward (m), y = height above the ground (m), pitch (rad, toes up > 0),
 * planted = foot on the ground and stationary in the world.
 */
export function footTarget(p: number, stance: number, cycle: number, lift: number): { f: number; y: number; pitch: number; planted: boolean } {
  const span = stance * cycle;
  if (p < stance) {
    const u = p / stance;
    // Late-stance heel lift (the foot rolls over the toe; the toe stays planted).
    const roll = u > 0.62 ? (u - 0.62) / 0.38 : 0;
    const heel = 0.06 * roll * roll;
    return { f: span * (0.5 - u), y: heel, pitch: -Math.asin(Math.min(0.9, heel / 0.16)), planted: true };
  }
  const u = (p - stance) / (1 - stance);
  const e = 0.5 - 0.5 * Math.cos(Math.PI * u);
  return { f: -span * 0.5 + span * e, y: lift * Math.sin(Math.PI * u) + 0.06 * (1 - u) * (1 - u) * (u < 0.3 ? 1 : 0), pitch: 0.25 * Math.sin(Math.PI * u) * (u > 0.5 ? 1 : -0.6), planted: false };
}

/**
 * Two-bone IK in the leg's sagittal plane. Target: forward f and down d from
 * the hip joint (d > 0). Returns hip and knee angles about +X (positive hip
 * swings the thigh forward; the knee bends with a negative angle).
 */
export function legIK(f: number, d: number): { hip: number; knee: number; reach: number } {
  const a = DIM.thigh;
  const b = DIM.shin;
  let dist = Math.hypot(f, d);
  const reach = dist;
  dist = clampN(dist, Math.abs(a - b) + 1e-3, REACH);
  const phi = Math.atan2(f, d);
  const cosK = clampN((a * a + b * b - dist * dist) / (2 * a * b), -1, 1);
  const bend = Math.PI - Math.acos(cosK);
  const cosA = clampN((a * a + dist * dist - b * b) / (2 * a * dist), -1, 1);
  const alpha = Math.acos(cosA);
  return { hip: phi + alpha, knee: -bend, reach };
}

function clampN(x: number, a: number, b: number): number {
  return x < a ? a : x > b ? b : x;
}
function smooth(a: number, b: number, x: number): number {
  const t = clampN((x - a) / (b - a), 0, 1);
  return t * t * (3 - 2 * t);
}
function approach(cur: number, target: number, dt: number, tau: number): number {
  return cur + (target - cur) * (1 - Math.exp(-dt / tau));
}

export class AvatarAnimator {
  state: AnimState = 'idle';
  /** Gait phase 0..1 (left leg; the right leg is half a cycle later). */
  phase = 0;
  /** Smoothed ground speed (m/s). */
  speed = 0;
  /** Seconds since the animation clock started (idle breathing). */
  time = 0;
  /** 0 = on the ground, 1 = fully in the air pose. */
  air = 0;
  /** Landing dip 0..1 and its timer. */
  landAmount = 0;
  landTimer = 0;
  /** Entries per state since creation (tests and diagnostics). */
  readonly entries: Record<AnimState, number> = { idle: 0, walk: 0, run: 0, jump: 0, fall: 0, land: 0 };
  /** Which feet are currently planted (stance and not rolling). */
  readonly planted: [boolean, boolean] = [false, false];
  /** Unreachable leg targets this frame (should stay 0 in normal walking). */
  overreach = 0;
  /** Per bone Euler XYZ (radians) and the hips' height offset (m) of the current pose. */
  readonly rot = new Float32Array(N * 3);
  hipsDrop = 0;
  private airTime = 0;
  private minVVert = 0;
  private wasGrounded = true;

  /** Advance the animation and write the pose (call applyTo afterwards). */
  update(inp: AnimInput): void {
    const dt = inp.dt;
    if (dt <= 0) return;
    this.time += dt;
    const instSpeed = Math.abs(inp.forwardDist) / dt;
    this.speed = approach(this.speed, inp.grounded ? instSpeed : this.speed, dt, 0.12);
    const g = gaitParams(this.speed);

    // Airborne bookkeeping and landing detection.
    if (!inp.grounded) {
      this.airTime += dt;
      this.minVVert = Math.min(this.minVVert, inp.vVert);
    }
    if (inp.grounded && !this.wasGrounded && this.airTime > 0.25) {
      this.landAmount = clampN(0.35 + Math.abs(this.minVVert) / 9, 0.35, 1);
      this.landTimer = 0.32 + 0.12 * this.landAmount;
    }
    if (inp.grounded) {
      this.airTime = 0;
      this.minVVert = 0;
    }
    this.wasGrounded = inp.grounded;
    this.landTimer = Math.max(0, this.landTimer - dt);
    const inAir = !inp.grounded && (this.airTime > 0.12 || inp.vVert > 0.5);
    this.air = approach(this.air, inAir ? 1 : 0, dt, inAir ? 0.08 : 0.05);

    // Gait phase follows the distance travelled; on the ground only.
    if (inp.grounded) {
      this.phase += inp.forwardDist / g.cycle;
      this.phase -= Math.floor(this.phase);
    }

    // State label.
    let st: AnimState;
    if (inAir) st = inp.vVert > 0 ? 'jump' : 'fall';
    else if (this.landTimer > 0) st = 'land';
    else if (this.speed < 0.25) st = 'idle';
    else if (this.speed < 5.8) st = 'walk';
    else st = 'run';
    if (st !== this.state) {
      this.state = st;
      this.entries[st]++;
    }
    this.pose(g, inp.vVert);
  }

  private pose(g: ReturnType<typeof gaitParams>, vVert: number): void {
    const r = this.rot;
    r.fill(0);
    const set = (b: number, x: number, y: number, z: number) => {
      r[b * 3] = x;
      r[b * 3 + 1] = y;
      r[b * 3 + 2] = z;
    };
    const add = (b: number, x: number, y: number, z: number, w: number) => {
      r[b * 3] += x * w;
      r[b * 3 + 1] += y * w;
      r[b * 3 + 2] += z * w;
    };
    const t = this.time;
    const amp = smooth(0.05, 0.9, this.speed);
    const ground = 1 - this.air;
    const land = this.landTimer > 0 ? this.landAmount * Math.sin((Math.PI * this.landTimer) / (0.32 + 0.12 * this.landAmount)) : 0;

    // ---- Ground pose: legs by IK from gait foot targets.
    const feet = [footTarget(this.phase, g.stance, g.cycle, g.lift), footTarget((this.phase + 0.5) % 1, g.stance, g.cycle, g.lift)];
    for (const ft of feet) {
      ft.f *= amp;
      ft.y *= amp;
      ft.pitch *= amp;
    }
    this.planted[0] = feet[0].planted && amp > 0.5 && feet[0].y < 1e-6;
    this.planted[1] = feet[1].planted && amp > 0.5 && feet[1].y < 1e-6;
    // Hip height: nominal crouch, lowered as needed so both feet stay reachable, plus the landing dip.
    let hipH = HIP_ABOVE_ANKLE - g.crouch * amp - 0.012 - land * 0.2;
    for (const ft of feet) hipH = Math.min(hipH, ft.y + Math.sqrt(Math.max(0, REACH * REACH - ft.f * ft.f)) - 1e-3);
    // Running bounce (both feet off the ground mid-flight).
    hipH += g.run * amp * 0.03 * Math.cos(4 * Math.PI * (this.phase - g.stance * 0.5));
    this.hipsDrop = (hipH - HIP_ABOVE_ANKLE) * ground;
    this.overreach = 0;
    const legBones = [
      [B.upperLegL, B.lowerLegL, B.footL],
      [B.upperLegR, B.lowerLegR, B.footR],
    ];
    for (let i = 0; i < 2; i++) {
      const ft = feet[i];
      const ik = legIK(ft.f, hipH - ft.y);
      if (ik.reach > REACH + 1e-3) this.overreach++;
      const [ul, ll, fb] = legBones[i];
      set(ul, ik.hip * ground, 0, (i === 0 ? -0.02 : 0.02) * ground);
      set(ll, ik.knee * ground, 0, 0);
      // Keep the sole flat to the ground plane, then apply the roll.
      set(fb, (-(ik.hip + ik.knee) + ft.pitch) * ground, 0, 0);
    }
    // Torso: forward lean with speed, counter-twist with the stride, breathing at rest.
    const swing = Math.sin(2 * Math.PI * this.phase);
    const lean = 0.03 + 0.05 * amp + 0.1 * g.run * amp;
    const breathe = (1 - amp) * Math.sin(t * 1.7);
    set(B.spine, (-lean * 0.5 + land * 0.12) * ground, 0.06 * swing * amp * ground, 0);
    set(B.chest, (-lean * 0.5 + 0.012 * breathe) * ground, 0.1 * swing * amp * ground, 0);
    set(B.hips, 0, -0.08 * swing * amp * ground, 0);
    set(B.head, (lean * 0.8 - land * 0.1) * ground, (-0.12 * swing * amp + 0.15 * (1 - amp) * Math.sin(t * 0.23)) * ground, 0);
    // Arms swing opposite to the legs; elbows bend more when running.
    const armAmp = (0.22 + 0.38 * g.run) * amp;
    const elbow = 0.2 + 0.22 * amp + 0.85 * g.run * amp;
    set(B.upperArmL, (-armAmp * swing + 0.02 * breathe) * ground, 0, (-0.1 - 0.03 * breathe - 0.08 * land) * ground);
    set(B.upperArmR, (armAmp * swing + 0.02 * breathe) * ground, 0, (0.1 + 0.03 * breathe + 0.08 * land) * ground);
    set(B.lowerArmL, (elbow + 0.15 * amp * Math.max(0, -swing)) * ground, 0, 0);
    set(B.lowerArmR, (elbow + 0.15 * amp * Math.max(0, swing)) * ground, 0, 0);
    set(B.handL, 0, 0.1 * ground, 0);
    set(B.handR, 0, -0.1 * ground, 0);

    // ---- Air pose: tucked jump while rising, open fall pose while descending.
    const w = this.air;
    if (w > 1e-4) {
      const fall = smooth(1.5, -3, vVert);
      const j = (1 - fall) * w;
      const f = fall * w;
      add(B.upperLegL, 0.85, 0, -0.04, j);
      add(B.lowerLegL, -1.25, 0, 0, j);
      add(B.footL, 0.35, 0, 0, j);
      add(B.upperLegR, 0.12, 0, 0.04, j);
      add(B.lowerLegR, -0.55, 0, 0, j);
      add(B.footR, 0.3, 0, 0, j);
      add(B.upperArmL, 0.55, 0, -0.35, j);
      add(B.upperArmR, -0.25, 0, 0.35, j);
      add(B.lowerArmL, 0.7, 0, 0, j);
      add(B.lowerArmR, 0.5, 0, 0, j);
      add(B.spine, -0.08, 0, 0, j);
      add(B.upperLegL, 0.4, 0, -0.08, f);
      add(B.lowerLegL, -0.65, 0, 0, f);
      add(B.footL, 0.2, 0, 0, f);
      add(B.upperLegR, 0.05, 0, 0.08, f);
      add(B.lowerLegR, -0.3, 0, 0, f);
      add(B.footR, 0.15, 0, 0, f);
      add(B.upperArmL, 0.25, 0, -1.0, f);
      add(B.upperArmR, 0.25, 0, 1.0, f);
      add(B.lowerArmL, 0.45, 0, 0, f);
      add(B.lowerArmR, 0.45, 0, 0, f);
      add(B.spine, 0.04, 0, 0, f);
      add(B.head, -0.12, 0, 0, f);
      // Small flutter so a long fall is not frozen.
      add(B.upperArmL, 0, 0, 0.06 * Math.sin(t * 7), f);
      add(B.upperArmR, 0, 0, -0.06 * Math.sin(t * 7 + 1), f);
    }
  }

  /** Write the current pose to the rig's bones (rest positions are kept). */
  applyTo(bones: Bone[], hipsRestY: number): void {
    const r = this.rot;
    for (let i = 0; i < N; i++) bones[i].rotation.set(r[i * 3], r[i * 3 + 1], r[i * 3 + 2]);
    bones[B.hips].position.y = hipsRestY + this.hipsDrop;
  }
}
