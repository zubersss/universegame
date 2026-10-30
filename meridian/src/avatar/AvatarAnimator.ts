import { Euler, Quaternion, Vector3, type Bone } from 'three';
import { B, BONE_NAMES, DIM } from './AvatarModel';

// Procedural, state-blended animation for the explorer.
//
// Ground locomotion: a gait planner (phase driven by the distance actually
// travelled, so stride is tied to ground speed) decides when each foot lifts
// and where it lands. A planted foot is locked to its ground point by the
// ball of the foot: it moves only by the body's own motion (forward, sideways
// and turning), so it never slides. Behind the body the heel lifts by rolling
// over that ball until the leg reaches it. Legs are solved with analytic
// two-bone IK; a per-foot ground query adapts feet to slopes and steps. When
// the body stops, short settle steps bring the feet back under it. Air and
// landing poses blend in on top. Everything is a pure function of the inputs
// and the animation clock.

export type AnimState = 'idle' | 'walk' | 'run' | 'jump' | 'fall' | 'land' | 'climb' | 'fly' | 'dash';

/** A power moving the body: flight (hover to cruise) or superspeed (dash), with its speed (m/s). */
export interface PowerMotion {
  mode: 'flight' | 'dash';
  speed: number;
}

/** Ground under a point, relative to the character's root plane. */
export interface FootGround {
  /** Ground height along up relative to the root (m; negative = below the feet point). */
  h: number;
  /** Ground slope along the foot (rad; positive = rising ahead). */
  pitch: number;
  /** Ground tilt across the foot (rad; positive = its normal leans to the foot's right, i.e. rising to the left). */
  roll: number;
}

/** Ground query: side 0 = left, 1 = right; forward and lateral offsets from the root (m); the foot's yaw (rad, left > 0) for the slope along it. */
export type GroundFn = (side: 0 | 1, forward: number, lateral: number, yaw: number) => FootGround | null;

export interface AnimInput {
  /** Frame time (s); 0 freezes the animation (pause). */
  dt: number;
  /** Signed distance moved along the facing direction this frame (m), measured before this frame's turn. */
  forwardDist: number;
  /** Signed distance moved to the right this frame (m), same basis. */
  lateralDist?: number;
  /** Body yaw change this frame (rad, left > 0), applied after the move. */
  turn?: number;
  grounded: boolean;
  /** Vertical speed along up (m/s). */
  vVert: number;
  /** Per-foot ground (slopes); omitted or null = flat ground at the root. */
  ground?: GroundFn | null;
  /** Where the camera looks relative to the body: yaw (rad, left > 0) and pitch (rad, up > 0). */
  lookYaw?: number;
  lookPitch?: number;
  /** Ladder climbing: blend 0..1 into the climb pose, phase in climb cycles (one cycle = two rungs). */
  climb?: { blend: number; phase: number } | null;
  /** A power moving the body (the ground gait pauses; feet re-plant afterwards). */
  power?: PowerMotion | null;
}

const N = BONE_NAMES.length;
const LEG = DIM.thigh + DIM.shin;
const REACH = LEG * 0.995;
/** Hip joint height above the ankle in the rest pose. */
const HIP_ABOVE_ANKLE = DIM.hipY - 0.02 - DIM.ankleY;
/** Lateral offset of each foot from the root (m). */
const FOOT_X = DIM.hipX + 0.015;
/** Ground pivot of the forefoot (ball to toe) ahead of the ankle when flat (m); the boot toe ends 1 cm beyond. */
export const BALL_F = 0.155;
const BALL_TO_ANKLE_LEN = Math.hypot(BALL_F, DIM.ankleY);
const BALL_TO_ANKLE_ANG = Math.atan2(DIM.ankleY, -BALL_F);
/** Most the heel can lift by rolling over the ball (rad). */
const MAX_ROLL = 1.05;
/** Heel contact behind the ankle when flat (m). */
const HEEL_B = 0.07;
const HEEL_TO_ANKLE_LEN = Math.hypot(HEEL_B, DIM.ankleY);
const HEEL_TO_ANKLE_ANG = Math.atan2(DIM.ankleY, HEEL_B);

export interface Gait {
  /** Cycle length (two steps, m). */
  cycle: number;
  /** Distance the body travels while one foot is planted (m). */
  span: number;
  /** Fraction of the cycle a foot is planted. */
  stance: number;
  /** Ankle position ahead of the hip at touchdown (m). */
  front: number;
  /** Swing foot clearance (m). */
  lift: number;
  /** Nominal knee bend as hip lowering (m). */
  crouch: number;
  /** 0 = walking, 1 = running. */
  run: number;
}

/**
 * Gait for a ground speed (m/s). Walking: ~1.4 m cycles at 1.4 m/s with a
 * foot down 62% of the time; running: longer cycles (~3.5 m at 4.5 m/s,
 * ~4.9 m at 7.5 m/s) with a short contact (~0.9 m of travel) and a flight phase.
 */
export function gaitParams(v: number): Gait {
  const run = smooth(1.9, 3.4, v);
  const walkCycle = 0.8 + 0.45 * v;
  const runCycle = 1.3 + 0.48 * v;
  const cycle = clampN(walkCycle + (runCycle - walkCycle) * run, 1.0, 5.2);
  const walkSpan = Math.min(0.62 * walkCycle, 0.95);
  const runSpan = clampN(0.8 + 0.025 * v, 0.85, 1.0);
  const span = walkSpan + (runSpan - walkSpan) * run;
  return {
    cycle,
    span,
    stance: clampN(span / cycle, 0.15, 0.66),
    front: Math.min(span * 0.42, 0.36),
    lift: 0.1 + 0.2 * run,
    crouch: 0.02 + 0.03 * smooth(0.2, 2, v) + 0.03 * run,
    run,
  };
}

/**
 * Planned ankle target for leg phase p in [0,1) relative to the point under
 * the hip: f = forward (m), y = height above its rest height (m), pitch (rad,
 * toes up > 0), stance = the foot should be on the ground.
 */
export function footTarget(p: number, g: Gait): { f: number; y: number; pitch: number; stance: boolean } {
  if (p < g.stance) {
    const u = p / g.stance;
    // Walking heel strike: toes up at touchdown, flat by 15% of the stance.
    const strike = (1 - g.run) * 0.18 * Math.max(0, 1 - u / 0.15);
    return { f: g.front - g.span * u, y: 0, pitch: strike, stance: true };
  }
  const u = (p - g.stance) / (1 - g.stance);
  return {
    f: g.front - g.span + g.span * ease(u),
    y: g.lift * Math.sin(Math.PI * Math.pow(u, 0.8)),
    // Toes down after push-off, through level at mid-swing, up before
    // touchdown, arriving at the walking heel-strike angle (continuous).
    pitch: -0.22 * Math.sin(2 * Math.PI * u) * (1 - u) + (1 - g.run) * 0.18 * smooth(0.55, 1, u),
    stance: false,
  };
}

/**
 * Two-bone leg IK, exact for the rig's bone order (upper leg Euler XYZ: hip
 * pitch outside, abduction about Z inside; the knee bends about X). Ankle
 * target from the hip joint: forward f, down d (> 0), lateral xr (right > 0).
 * Returns hip pitch (positive swings the thigh forward), abduction, knee
 * (negative = bent) and the unclamped distance; unreachable targets are
 * scaled onto the reachable sphere.
 */
export function legIK(f: number, d: number, xr = 0): { hip: number; abd: number; knee: number; reach: number } {
  const a = DIM.thigh;
  const b = DIM.shin;
  const reach = Math.hypot(f, d, xr);
  const dist = clampN(reach, Math.abs(a - b) + 0.05, REACH);
  const s = dist / Math.max(reach, 1e-9);
  const tf = f * s;
  const td = d * s;
  const tx = xr * s;
  const knee = -(Math.PI - Math.acos(clampN((a * a + b * b - dist * dist) / (2 * a * b), -1, 1)));
  // Chain in the upper leg's frame: extent along -Y and along +Z (backward).
  const ell = a + b * Math.cos(knee);
  const cz = -b * Math.sin(knee);
  const abd = Math.asin(clampN(tx / ell, -1, 1));
  // Rotate (y, z) = (-ell cos abd, cz) onto (-td, -tf) about X.
  const vy = -ell * Math.cos(abd);
  const ty = -td;
  const tz = -tf;
  const hip = Math.atan2(vy * tz - cz * ty, vy * ty + cz * tz);
  return { hip, abd, knee, reach };
}

/**
 * Ankle position (forward, height above its rest height) for a foot whose
 * ball is at (fb, hb) on the ground, rotated by psi about the ball (toes up > 0).
 */
export function ankleFromBall(fb: number, hb: number, psi: number): { f: number; y: number } {
  const a = BALL_TO_ANKLE_ANG + psi;
  return { f: fb + BALL_TO_ANKLE_LEN * Math.cos(a), y: hb + BALL_TO_ANKLE_LEN * Math.sin(a) - DIM.ankleY };
}

/** Ankle position for a foot pivoting on its heel at (fh, hh), rotated by psi (toes up > 0). */
export function ankleFromHeel(fh: number, hh: number, psi: number): { f: number; y: number } {
  const a = HEEL_TO_ANKLE_ANG + psi;
  return { f: fh + HEEL_TO_ANKLE_LEN * Math.cos(a), y: hh + HEEL_TO_ANKLE_LEN * Math.sin(a) - DIM.ankleY };
}

function clampN(x: number, a: number, b: number): number {
  return x < a ? a : x > b ? b : x;
}
function smooth(a: number, b: number, x: number): number {
  const t = clampN((x - a) / (b - a), 0, 1);
  return t * t * (3 - 2 * t);
}
function ease(u: number): number {
  return 0.5 - 0.5 * Math.cos(Math.PI * clampN(u, 0, 1));
}
function approach(cur: number, target: number, dt: number, tau: number): number {
  return cur + (target - cur) * (1 - Math.exp(-dt / tau));
}

const _qa = new Quaternion();
const _qb = new Quaternion();
const _e = new Euler();
const _ax = new Vector3(1, 0, 0);
const _ay = new Vector3(0, 1, 0);
const _az = new Vector3(0, 0, 1);

const LAND_TIME = (amount: number) => 0.32 + 0.12 * amount;
/** Settle step: duration (s) and lift (m). */
const SETTLE_T = 0.26;
const SETTLE_LIFT = 0.07;

/** Per-foot lock: a planted foot keeps its ground point while the body moves. */
interface FootLock {
  locked: boolean;
  /** Locked ankle position when the foot is flat (root frame: forward, lateral; m). */
  f: number;
  x: number;
  /** Start of the current swing or settle step. */
  sf: number;
  sx: number;
  /** Remaining time of a settle step (s); 0 = none. */
  settle: number;
  /** Settle step target. */
  tf: number;
  tx: number;
  /** Ankle target used last frame. */
  cf: number;
  cx: number;
  /** Foot yaw relative to the body (rad, left > 0): a planted foot keeps its world direction while the body turns. */
  yaw: number;
  /** Yaw at the start of the current swing or settle step, and last frame's. */
  syaw: number;
  cyaw: number;
  /** Foot pitch relative to the ground at the start of the swing (toe-off roll) and last frame's. */
  spitch: number;
  cpitch: number;
}

function newLock(x: number): FootLock {
  return { locked: true, f: 0, x, sf: 0, sx: x, settle: 0, tf: 0, tx: x, cf: 0, cx: x, yaw: 0, syaw: 0, cyaw: 0, spitch: 0, cpitch: 0 };
}

/** A planted foot twisted further than this from the body takes a step. */
const MAX_FOOT_YAW = 0.6;

interface FootPose {
  f: number;
  x: number;
  /** Ankle height above its rest height (m); before posing, a swing foot's lift above the ground. */
  y: number;
  /** Foot rotation (rad, toes up > 0). */
  pitch: number;
  /** Planted: locked to its ground point. */
  planted: boolean;
  /** Walking heel strike (rad, toes up): the foot pivots on its heel. */
  strike: number;
  /** Progress through the stance 0..1 (planted feet; drives the planned heel lift). */
  stanceU: number;
  /** Foot yaw relative to the body (rad, left > 0). */
  yaw: number;
  /** Ground under the ball of a planted foot. */
  gh: number;
  gp: number;
  /** Ground roll under the foot (see FootGround.roll). */
  gr: number;
}

export class AvatarAnimator {
  state: AnimState = 'idle';
  /** Gait phase 0..1 (left leg; the right leg is half a cycle later). */
  phase = 0;
  /** Smoothed ground speed (m/s). */
  speed = 0;
  /** Seconds of animation time (idle breathing, flutter). */
  time = 0;
  /** 0 = on the ground, 1 = fully in the air pose. */
  air = 0;
  /** Landing dip 0..1 and its remaining time (s). */
  landAmount = 0;
  landTimer = 0;
  /** Air pose: 0 rising (jump) .. 1 falling. */
  fallMix = 0;
  /** Entries per state since creation (tests and diagnostics). */
  readonly entries: Record<AnimState, number> = { idle: 0, walk: 0, run: 0, jump: 0, fall: 0, land: 0, climb: 0, fly: 0, dash: 0 };
  /** Blend into the flight and dash poses (0..1) and the dash's own stride phase. */
  fly = 0;
  dash = 0;
  dashPhase = 0;
  /** Speed of the power moving the body (m/s), smoothed. */
  powerSpeed = 0;
  /** Which feet are planted this frame (ball on its locked ground point). */
  readonly planted: [boolean, boolean] = [false, false];
  /** Legs that could not reach their target this frame (0 on walkable ground). */
  overreach = 0;
  /** Settle steps taken (diagnostics). */
  settleSteps = 0;
  /** Smoothed ground slope along the facing (rad, rising ahead > 0). */
  slope = 0;
  /** Per bone Euler XYZ (radians) of the current pose, and the hips' height offset (m). */
  readonly rot = new Float32Array(N * 3);
  hipsDrop = 0;
  private airTime = 0;
  private minVVert = 0;
  private wasGrounded = true;
  private headYaw = 0;
  private headPitch = 0;
  private poweredLast = false;
  private readonly locks: [FootLock, FootLock] = [newLock(-FOOT_X), newLock(FOOT_X)];

  /** Advance the animation and compute the pose (write it with applyTo). */
  update(input: AnimInput): void {
    const dt = input.dt;
    if (!(dt > 0)) return;
    this.time += dt;
    // A power moving the body: blend its pose in, pause the ground gait (the
    // feet do not follow a 100 m/s body) and re-plant the feet when it ends.
    const pw = input.power ?? null;
    this.fly = approach(this.fly, pw && pw.mode === 'flight' ? 1 : 0, dt, 0.15);
    this.dash = approach(this.dash, pw && pw.mode === 'dash' ? 1 : 0, dt, 0.1);
    if (pw) this.powerSpeed = approach(this.powerSpeed, pw.speed, dt, 0.2);
    if (pw && pw.mode === 'dash') this.dashPhase = (this.dashPhase + dt * Math.min(3.4, 1.2 + pw.speed / 30)) % 1;
    if (this.poweredLast && !pw) this.resetFeet();
    this.poweredLast = !!pw;
    const inp: AnimInput = pw ? { ...input, forwardDist: 0, lateralDist: 0, turn: 0, grounded: true, vVert: 0 } : input;
    const instSpeed = Math.abs(inp.forwardDist) / dt;
    if (inp.grounded) this.speed = approach(this.speed, instSpeed, dt, 0.12);
    const g = gaitParams(this.speed);
    // Shorter strides on slopes keep the downhill foot within reach.
    const k = 1 / (1 + 1.3 * Math.abs(Math.tan(this.slope)));
    g.cycle *= k;
    g.span *= k;
    g.front *= k;

    // Airborne bookkeeping and landing detection. Not under a power: its
    // neutral ground input is no landing (flight starts mid-jump), and the air
    // pose fades slowly under the power pose instead of snapping to a stance.
    let inAir = false;
    if (pw) {
      this.airTime = 0;
      this.minVVert = 0;
      this.wasGrounded = true;
      this.landTimer = 0;
      this.air = approach(this.air, 0, dt, 0.3);
    } else {
      if (!inp.grounded) {
        this.airTime += dt;
        this.minVVert = Math.min(this.minVVert, inp.vVert);
      }
      if (inp.grounded && !this.wasGrounded && this.airTime > 0.25) {
        this.landAmount = clampN(0.35 + Math.abs(this.minVVert) / 9, 0.35, 1);
        this.landTimer = LAND_TIME(this.landAmount);
      }
      if (inp.grounded) {
        this.airTime = 0;
        this.minVVert = 0;
      }
      this.wasGrounded = inp.grounded;
      this.landTimer = Math.max(0, this.landTimer - dt);
      // Short ungrounded moments (stepping off a ledge, a bump) keep the gait.
      inAir = !inp.grounded && (this.airTime > 0.12 || inp.vVert > 0.5);
      this.air = approach(this.air, inAir ? 1 : 0, dt, inAir ? 0.08 : 0.05);
      // Jump/fall mix of the air pose: follows the vertical speed in the air
      // and holds on touchdown, so the air pose fades out as it was (the speed
      // drops to zero at once on landing).
      if (inAir) this.fallMix = approach(this.fallMix, smooth(1.5, -3, inp.vVert), dt, 0.06);
    }

    // Standing with both feet under the body: line the gait up so that the
    // first step starts from where the feet actually are.
    const [l0, l1] = this.locks;
    if (this.speed < 0.25 && inp.grounded && l0.locked && l1.locked && l0.settle === 0 && l1.settle === 0 && Math.abs(l0.f) < 0.06 && Math.abs(l1.f) < 0.06) {
      this.phase = g.stance * clampN(g.front / g.span, 0, 1);
    }
    // Gait phase follows the distance travelled, on the ground only.
    if (inp.grounded) {
      this.phase += inp.forwardDist / g.cycle;
      this.phase -= Math.floor(this.phase);
    }
    // Head follows the camera's look direction within comfortable limits.
    this.headYaw = approach(this.headYaw, clampN(inp.lookYaw ?? 0, -1.0, 1.0), dt, 0.12);
    this.headPitch = approach(this.headPitch, clampN(inp.lookPitch ?? 0, -0.6, 0.5), dt, 0.12);

    let st: AnimState;
    if (pw) st = pw.mode === 'flight' ? 'fly' : 'dash';
    else if (inp.climb && inp.climb.blend > 0.5) st = 'climb';
    else if (inAir) st = inp.vVert > 0 ? 'jump' : 'fall';
    else if (this.landTimer > 0) st = 'land';
    else if (this.speed < 0.25) st = 'idle';
    else if (this.speed < 5.8) st = 'walk';
    else st = 'run';
    if (st !== this.state) {
      this.state = st;
      this.entries[st]++;
    }
    this.pose(g, inp, instSpeed > 0.2);
  }

  /** Foot targets for this frame (locks, swing, settle steps, ground). */
  private feet(g: Gait, amp: number, inp: AnimInput, moving: boolean): FootPose[] {
    const df = inp.forwardDist;
    const dx = inp.lateralDist ?? 0;
    const th = inp.turn ?? 0;
    const ct = Math.cos(th);
    const sn = Math.sin(th);
    // Settle steps only once the body has actually stopped.
    const idle = amp < 0.3 && !moving;
    const out: FootPose[] = [];
    let settling = this.locks[0].settle > 0 || this.locks[1].settle > 0;
    let slopeSum = 0;
    let slopeN = 0;
    for (let i = 0; i < 2; i++) {
      const L = this.locks[i];
      const x0 = i === 0 ? -FOOT_X : FOOT_X;
      if (L.locked) {
        // The world-fixed point (and direction) seen from the moved and turned body.
        const a = L.f - df;
        const b = L.x - dx;
        L.f = a * ct - b * sn;
        L.x = a * sn + b * ct;
        L.yaw -= th;
      }
      const p = i === 0 ? this.phase : (this.phase + 0.5) % 1;
      const plan = footTarget(p, g);
      plan.f *= amp;
      plan.y *= amp;
      plan.pitch *= amp;
      const fp: FootPose = { f: plan.f, x: x0, y: plan.y, pitch: plan.pitch, planted: false, strike: 0, stanceU: 0, yaw: 0, gh: 0, gp: 0, gr: 0 };
      if (this.air > 0.5) {
        // Airborne: no ground contact; the air pose takes over the legs.
        L.locked = false;
        L.settle = 0;
        L.sf = L.cf;
        L.sx = L.cx;
        L.syaw = L.cyaw;
        L.spitch = L.cpitch;
      } else {
        if (L.settle === 0) {
          const far = L.locked && (Math.abs(L.x - x0) > 0.24 || L.f > 0.6 || L.f < -0.95 || Math.abs(L.yaw) > MAX_FOOT_YAW);
          const offRest = L.locked ? Math.abs(L.f) > 0.05 || Math.abs(L.x - x0) > 0.04 || Math.abs(L.yaw) > 0.15 : true;
          // Idle settling goes one foot at a time; a foot left far behind (or
          // twisted) may start once the other foot is halfway through its step.
          const other = this.locks[1 - i];
          const free = far ? other.settle < SETTLE_T * 0.5 : !settling;
          if (free && (far || (idle && offRest))) {
            L.sf = L.locked ? L.f : L.cf;
            L.sx = L.locked ? L.x : L.cx;
            L.syaw = L.locked ? L.yaw : L.cyaw;
            L.spitch = L.cpitch;
            L.tf = idle ? 0 : clampN(plan.f, -0.25, 0.25);
            L.tx = x0;
            L.locked = false;
            L.settle = SETTLE_T;
            settling = true;
            this.settleSteps++;
          }
        }
        if (L.settle > 0) {
          const u = 1 - L.settle / SETTLE_T;
          const e = ease(u);
          fp.f = L.sf + (L.tf - L.sf) * e;
          fp.x = L.sx + (L.tx - L.sx) * e;
          fp.y = SETTLE_LIFT * Math.sin(Math.PI * u);
          fp.pitch = L.spitch * (1 - e);
          fp.yaw = L.syaw * (1 - e);
          L.settle = Math.max(0, L.settle - inp.dt);
          if (L.settle === 0) {
            L.locked = true;
            L.f = L.tf;
            L.x = L.tx;
            L.yaw = 0;
          }
        } else if (plan.stance || (idle && L.locked)) {
          // Planted (a standing foot stays planted whatever the planner says).
          if (!L.locked) {
            L.locked = true;
            L.f = plan.f;
            L.x = x0;
            L.yaw = 0;
          }
          fp.f = L.f;
          fp.x = L.x;
          fp.yaw = L.yaw;
          fp.planted = true;
          fp.strike = plan.pitch;
          fp.pitch = 0;
          fp.stanceU = plan.stance ? p / g.stance : 0;
        } else {
          if (L.locked) {
            L.locked = false;
            L.sf = L.f;
            L.sx = L.x;
            L.syaw = L.yaw;
            L.spitch = L.cpitch;
          }
          const u = (p - g.stance) / (1 - g.stance);
          const e = ease(u);
          // Forward travel: a cubic whose end slopes partly follow the ground
          // moving past the body (half its speed), so the foot leaves and
          // lands without a velocity jump (a little kick-back after lift-off,
          // a little retraction before touchdown).
          const m = -0.5 * (g.cycle - g.span) * amp;
          const u2 = u * u;
          const u3 = u2 * u;
          fp.f = (2 * u3 - 3 * u2 + 1) * L.sf + (u3 - 2 * u2 + u) * m + (-2 * u3 + 3 * u2) * g.front * amp + (u3 - u2) * m;
          fp.x = L.sx + (x0 - L.sx) * e;
          fp.yaw = L.syaw * (1 - e);
          // Leave the ground still rolled (toe-off), then follow the swing's own pitch.
          const w = ease(Math.min(1, u / 0.3));
          fp.pitch = L.spitch * (1 - w) + plan.pitch * w;
        }
      }
      L.cf = fp.f;
      L.cx = fp.x;
      L.cyaw = fp.yaw;
      // Ground under the ball of the foot (along its own axis). Every foot is
      // posed about that point (see place() in pose()), so a swing foot
      // touches down exactly where its planted pose begins.
      const gq = inp.ground ? inp.ground(i as 0 | 1, fp.f + BALL_F * Math.cos(fp.yaw), fp.x - BALL_F * Math.sin(fp.yaw), fp.yaw) : null;
      if (gq) {
        fp.gh = clampN(gq.h, -0.8, 0.8);
        fp.gp = clampN(gq.pitch, -0.85, 0.85);
        fp.gr = clampN(gq.roll, -0.85, 0.85);
        slopeSum += fp.gp;
        slopeN++;
      }
      out.push(fp);
    }
    this.slope = approach(this.slope, slopeN ? slopeSum / slopeN : 0, inp.dt, 0.25);
    return out;
  }

  private pose(g: Gait, inp: AnimInput, moving: boolean): void {
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
    const land = this.landTimer > 0 ? this.landAmount * Math.sin((Math.PI * this.landTimer) / LAND_TIME(this.landAmount)) : 0;
    const feet = this.feet(g, amp, inp, moving);

    // Hip height: nominal crouch; walking dips at double support, running
    // compresses at mid-stance and rises in flight; plus the landing dip.
    const p = this.phase;
    const walkBob = -0.022 * (1 - g.run) * amp * (0.5 + 0.5 * Math.cos(4 * Math.PI * p));
    const runBob = 0.035 * g.run * amp * Math.cos(4 * Math.PI * (p - g.stance * 0.5 - 0.25));
    let hipH = HIP_ABOVE_ANKLE - g.crouch * amp - 0.012 + walkBob + runBob - land * 0.2;
    // Planted feet pivot about a ground point along their own axis (which may
    // be twisted from the body by a turn): the heel at touchdown, the ball
    // otherwise. place() gives the ankle for a rotation psi about that point.
    const hipXOf = (i: number) => (i === 0 ? -DIM.hipX : DIM.hipX);
    const place = (ft: FootPose, psi: number, heel: boolean) => {
      const cy = Math.cos(ft.yaw);
      const sy = Math.sin(ft.yaw);
      // Ball of the foot in the body frame (forward, right); the foot axis
      // points (cy, -sy) and the foot's right (sy, cy).
      const bf = ft.f + BALL_F * cy;
      const bx = ft.x - BALL_F * sy;
      // The foot bone turns by yaw, then rolls with the ground across the
      // foot, then pitches by psi about its (tilted) ball line, so the ball
      // line stays on the ground and the ankle leans sideways with the roll.
      const sp = Math.sin(psi);
      const cp = Math.cos(psi);
      const sr = Math.sin(ft.gr);
      const cr = Math.cos(ft.gr);
      let along: number;
      let up: number;
      // Pivot point relative to the ball: (along the foot, to its right, up).
      let pf = 0;
      let px = 0;
      let py = 0;
      if (heel) {
        // Pivot on the heel, which lies on the ground a foot-length back along the
        // sole's ground direction (cos p, sin p sin r, sin p cos r).
        const len = BALL_F + HEEL_B;
        const sg = Math.sin(ft.gp);
        pf = -len * Math.cos(ft.gp);
        px = -len * sg * sr;
        py = -len * sg * cr;
        along = HEEL_B * cp - DIM.ankleY * sp;
        up = DIM.ankleY * cp + HEEL_B * sp;
      } else {
        // Pivot on the ball.
        along = -(DIM.ankleY * sp + BALL_F * cp);
        up = DIM.ankleY * cp - BALL_F * sp;
      }
      const a = pf + along;
      const lat = px + up * sr;
      return { f: bf + a * cy + lat * sy, x: bx - a * sy + lat * cy, y: ft.gh + py + up * cr - DIM.ankleY };
    };
    // Lower the hips only where a planted foot cannot be reached otherwise
    // (it may first roll onto its ball, by up to MAX_ROLL). Swing feet are in
    // the air: an out-of-reach swing target is simply clamped.
    for (let i = 0; i < 2; i++) {
      const ft = feet[i];
      if (!ft.planted) continue;
      const a = ft.strike > 0 ? place(ft, ft.gp + ft.strike, true) : place(ft, ft.f < 0 ? ft.gp - MAX_ROLL : ft.gp, false);
      const xr = a.x - hipXOf(i);
      hipH = Math.min(hipH, a.y + Math.sqrt(Math.max(0, REACH * REACH - a.f * a.f - xr * xr)) - 1e-3);
    }
    // Planted feet: pivot on the heel at touchdown, else the least roll that reaches.
    for (let i = 0; i < 2; i++) {
      const ft = feet[i];
      if (!ft.planted) continue;
      let psi: number;
      let heel = false;
      if (ft.strike > 0) {
        psi = ft.gp + ft.strike;
        heel = true;
      } else {
        const reachAt = (roll: number) => {
          const a = place(ft, ft.gp - roll, false);
          return Math.hypot(a.f, hipH - a.y, a.x - hipXOf(i));
        };
        // The heel starts lifting in the second half of the stance (more when
        // running), and at least as much as the leg needs to reach.
        let roll = (0.35 + 0.45 * g.run) * amp * smooth(0.4, 1, ft.stanceU);
        if (reachAt(roll) > REACH) {
          let lo = roll;
          let hi = MAX_ROLL;
          for (let k = 0; k < 16; k++) {
            const mid = (lo + hi) / 2;
            if (reachAt(mid) > REACH) lo = mid;
            else hi = mid;
          }
          roll = hi;
        }
        psi = ft.gp - roll;
      }
      const a = place(ft, psi, heel);
      ft.f = a.f;
      ft.x = a.x;
      ft.y = a.y;
      ft.pitch = psi;
    }
    // Swing and settle feet: the same geometry, lifted (y holds the lift so
    // far), pivoting on the ball when the toes point down and on the heel when
    // they point up, so lift-off and touchdown match the planted poses.
    for (const ft of feet) {
      if (ft.planted) continue;
      const psi = ft.gp + ft.pitch;
      const a = place(ft, psi, ft.pitch > 0);
      ft.f = a.f;
      ft.x = a.x;
      ft.y = a.y + ft.y;
      ft.pitch = psi;
    }
    for (let i = 0; i < 2; i++) this.locks[i].cpitch = feet[i].pitch - feet[i].gp;
    const xr = [feet[0].x - hipXOf(0), feet[1].x - hipXOf(1)];
    this.hipsDrop = (hipH - HIP_ABOVE_ANKLE) * ground;
    this.overreach = 0;
    const legBones = [
      [B.upperLegL, B.lowerLegL, B.footL],
      [B.upperLegR, B.lowerLegR, B.footR],
    ];
    for (let i = 0; i < 2; i++) {
      const ft = feet[i];
      const ik = legIK(ft.f, hipH - ft.y, xr[i]);
      if (ft.planted && ik.reach > REACH + 2e-3) this.overreach++;
      const [ul, ll, fb] = legBones[i];
      set(ul, ik.hip * ground, 0, ik.abd * ground);
      set(ll, ik.knee * ground, 0, 0);
      // Foot: its pitch relative to the body (roll, heel strike, slope), with
      // the leg's own rotation removed exactly.
      _qa.setFromEuler(_e.set(ik.hip, 0, ik.abd));
      _qb.setFromAxisAngle(_ax, ik.knee);
      _qa.multiply(_qb).invert();
      _qb.setFromAxisAngle(_ay, ft.yaw * ground);
      _qa.multiply(_qb);
      // Roll with the ground about the foot's forward axis (-Z; the sole's normal leans to its right for positive roll) ...
      _qb.setFromAxisAngle(_az, -ft.gr * ground);
      _qa.multiply(_qb);
      // ... then pitch about the tilted ball line.
      _qb.setFromAxisAngle(_ax, ft.pitch);
      _e.setFromQuaternion(_qa.multiply(_qb), 'XYZ');
      set(fb, _e.x * ground, _e.y * ground, _e.z * ground);
      this.planted[i] = ft.planted && ft.strike === 0 && this.air < 0.01;
    }

    // Torso: forward lean with speed (and uphill), counter-twist with the
    // stride, breathing at rest. sw > 0 while the right foot is ahead: the
    // left arm and shoulder come forward.
    const sw = clampN((feet[1].f - feet[0].f) / Math.max(0.05, g.span * amp * 0.9), -1, 1) * amp;
    const lean = 0.03 + 0.05 * amp + 0.12 * g.run * amp + 0.35 * Math.max(0, this.slope) * amp;
    const breathe = (1 - amp) * Math.sin(t * 1.7);
    set(B.spine, (-lean * 0.5 + land * 0.12) * ground, -0.05 * sw * ground, 0);
    set(B.chest, (-lean * 0.5 + 0.012 * breathe) * ground, -0.09 * sw * ground, 0);
    const idleLook = 0.12 * (1 - amp) * Math.sin(t * 0.23);
    set(B.head, (lean * 0.8 - land * 0.1) * ground + this.headPitch, (0.13 * sw + idleLook) * ground + this.headYaw, 0);
    // Arms swing opposite to the legs; elbows bend more when running.
    const armAmp = 0.24 + 0.4 * g.run;
    const elbow = 0.2 + 0.22 * amp + 0.95 * g.run * amp;
    set(B.upperArmL, (armAmp * sw + 0.02 * breathe) * ground, 0, (-0.1 - 0.03 * breathe - 0.08 * land) * ground);
    set(B.upperArmR, (-armAmp * sw + 0.02 * breathe) * ground, 0, (0.1 + 0.03 * breathe + 0.08 * land) * ground);
    set(B.lowerArmL, (elbow + 0.15 * Math.max(0, sw)) * ground, 0, 0);
    set(B.lowerArmR, (elbow + 0.15 * Math.max(0, -sw)) * ground, 0, 0);
    set(B.handL, 0, 0.1 * ground, 0);
    set(B.handR, 0, -0.1 * ground, 0);

    // ---- Air pose: tucked jump while rising, open fall pose while descending.
    const w = this.air;
    if (w > 1e-4) {
      const fall = this.fallMix;
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

    // ---- Ladder climb: hand over hand, knees lifting in turn, leaning in.
    const cb = inp.climb ? clampN(inp.climb.blend, 0, 1) : 0;
    if (cb > 1e-4) {
      const ph = 2 * Math.PI * (inp.climb!.phase % 1);
      const l = 0.5 + 0.5 * Math.sin(ph);
      const rr = 1 - l;
      const climbPose: [number, number, number, number][] = [
        [B.spine, -0.14, 0, 0],
        [B.chest, -0.06, 0, 0],
        [B.head, 0.25, 0, 0],
        [B.upperArmL, 2.25 + 0.45 * l, 0, -0.18],
        [B.upperArmR, 2.25 + 0.45 * rr, 0, 0.18],
        [B.lowerArmL, 1.05 - 0.5 * l, 0, 0],
        [B.lowerArmR, 1.05 - 0.5 * rr, 0, 0],
        [B.handL, 0, 0.3, 0],
        [B.handR, 0, -0.3, 0],
        [B.upperLegL, 0.3 + 0.75 * rr, 0, -0.05],
        [B.upperLegR, 0.3 + 0.75 * l, 0, 0.05],
        [B.lowerLegL, -0.45 - 1.05 * rr, 0, 0],
        [B.lowerLegR, -0.45 - 1.05 * l, 0, 0],
        [B.footL, 0.15 + 0.3 * rr, 0, 0],
        [B.footR, 0.15 + 0.3 * l, 0, 0],
      ];
      for (let i = 0; i < r.length; i++) r[i] *= 1 - cb;
      for (const [b, x, y, z] of climbPose) add(b, x, y, z, cb);
      this.hipsDrop *= 1 - cb;
      // Hands and feet are on the ladder, not planted on the ground.
      this.planted[0] = this.planted[1] = false;
    }

    // ---- Powers: flight (hover stance blending into a streamlined cruise)
    // and superspeed (a stylised dash at a capped cadence, leaning in).
    const fw = this.fly;
    const dw = this.dash;
    if (fw > 1e-4 || dw > 1e-4) {
      const keep = 1 - Math.max(fw, dw);
      for (let i = 0; i < r.length; i++) r[i] *= keep;
      this.hipsDrop *= keep;
      this.planted[0] = this.planted[1] = false;
    }
    if (fw > 1e-4) {
      const c = smooth(5, 60, this.powerSpeed); // 0 hover .. 1 cruise
      const h = (1 - c) * fw;
      const k = c * fw;
      const sway = Math.sin(t * 1.3);
      // Hover: knees soft, toes down, arms out for balance.
      add(B.upperLegL, 0.18 + 0.03 * sway, 0, -0.05, h);
      add(B.upperLegR, 0.05 - 0.03 * sway, 0, 0.05, h);
      add(B.lowerLegL, -0.45, 0, 0, h);
      add(B.lowerLegR, -0.25, 0, 0, h);
      add(B.footL, -0.35, 0, 0, h);
      add(B.footR, -0.3, 0, 0, h);
      add(B.upperArmL, 0.2, 0, -0.5 - 0.05 * sway, h);
      add(B.upperArmR, 0.2, 0, 0.5 + 0.05 * sway, h);
      add(B.lowerArmL, 0.35, 0, 0, h);
      add(B.lowerArmR, 0.35, 0, 0, h);
      // Cruise (the body itself is pitched forward by the Avatar): legs
      // together and pointed, arms swept back, head up to see ahead.
      add(B.upperLegL, -0.04, 0, 0.03, k);
      add(B.upperLegR, -0.04, 0, -0.03, k);
      add(B.lowerLegL, -0.12, 0, 0, k);
      add(B.lowerLegR, -0.08, 0, 0, k);
      add(B.footL, -0.65, 0, 0, k);
      add(B.footR, -0.65, 0, 0, k);
      add(B.upperArmL, -0.35, 0, -0.16, k);
      add(B.upperArmR, -0.35, 0, 0.16, k);
      add(B.lowerArmL, 0.12, 0, 0, k);
      add(B.lowerArmR, 0.12, 0, 0, k);
      add(B.head, 0.75, 0, 0, k);
      add(B.spine, 0.05, 0, 0, k);
    }
    if (dw > 1e-4) {
      // A sprinter's stride, legs and arms driving hard, leaning into the run.
      const ph = 2 * Math.PI * this.dashPhase;
      const sL = Math.sin(ph);
      const sR = Math.sin(ph + Math.PI);
      const leg = (s1: number) => [0.25 + 0.75 * s1, -1.0 - 0.7 * Math.max(0, -s1) - 0.4 * Math.max(0, s1), 0.3 * s1];
      const [hl, kl, fl] = leg(sL);
      const [hr, kr, fr] = leg(sR);
      add(B.upperLegL, hl, 0, -0.03, dw);
      add(B.upperLegR, hr, 0, 0.03, dw);
      add(B.lowerLegL, kl, 0, 0, dw);
      add(B.lowerLegR, kr, 0, 0, dw);
      add(B.footL, fl, 0, 0, dw);
      add(B.footR, fr, 0, 0, dw);
      add(B.upperArmL, -0.9 * sL, 0, -0.12, dw);
      add(B.upperArmR, -0.9 * sR, 0, 0.12, dw);
      add(B.lowerArmL, 1.35, 0, 0, dw);
      add(B.lowerArmR, 1.35, 0, 0, dw);
      add(B.spine, -0.3, 0, 0, dw);
      add(B.chest, -0.2, -0.12 * sL, 0, dw);
      add(B.head, 0.42, 0, 0, dw);
      this.hipsDrop -= 0.08 * dw;
    }
  }

  /** Forget any airborne state (the body was placed, not dropped): no landing follows. */
  resetAir(): void {
    this.air = 0;
    this.airTime = 0;
    this.minVVert = 0;
    this.wasGrounded = true;
    this.landTimer = 0;
  }

  /** Re-plant both feet at rest under the body (after a scripted move such as a ladder climb). */
  resetFeet(): void {
    this.locks[0] = newLock(-FOOT_X);
    this.locks[1] = newLock(FOOT_X);
    this.speed = 0;
  }

  /** Write the current pose to the rig's bones (rest positions are kept). */
  applyTo(bones: Bone[], hipsRestY: number): void {
    const r = this.rot;
    for (let i = 0; i < N; i++) bones[i].rotation.set(r[i * 3], r[i * 3 + 1], r[i * 3 + 2]);
    bones[B.hips].position.y = hipsRestY + this.hipsDrop;
  }
}
