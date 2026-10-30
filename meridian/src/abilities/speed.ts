import { Quaternion, Vector3 } from 'three';
import { SPEED_EXIT_MAX, type SpeedParams } from './types';

// The speed primitive (Redline; Sunline Dash is a burst variant). Charter K:
// hold Q while grounded to run, steer with the look (yaw rate falls from
// 3 to 0.8 rad/s with speed), X or releasing Q brakes. Charter J: every
// step the path ahead is checked (swept capsule for walls, ground probes for
// slopes steeper than the limit and for ledges), and the speed never exceeds
// what the braking curve can stop before the nearest such obstacle; where
// collision ahead is not loaded the speed is limited instead of stalling.
// Walkable rises and descents are run along, not stopped at. Leaving
// superspeed always passes through braking down to sprint speed.

export interface SpeedInput {
  /** Q held. */
  run: boolean;
  /** X held. */
  brake: boolean;
}

/** Ground found ahead: height relative to the feet (m) and slope (deg). */
export interface GroundAhead {
  h: number;
  slopeDeg: number;
}

export interface SpeedSense {
  up: Vector3;
  /** Camera heading (tangent plane): the course turns toward it. */
  heading: Vector3;
  grounded: boolean;
  /** Ground normal under the feet (null when airborne or unknown). */
  normal: Vector3 | null;
  /** Free distance along a direction for the walker's capsule lifted above the ground (Infinity when clear); the hit surface's normal into `normal`. */
  clear(dir: Vector3, dist: number, normal?: Vector3): number;
  /**
   * Terrain `ahead` metres along a tangent direction, searched from `top`
   * down to `bottom` (heights along up relative to the feet); null when there
   * is none in that span. The shape of the land only: props and the ship
   * are walls for the capsule sweep.
   */
  ground(dir: Vector3, ahead: number, top: number, bottom: number): GroundAhead | null;
  /** Collision is loaded `dist` metres along the course (charter J readiness). */
  ready(dist: number): boolean;
  /** Gravity (m/s^2) while airborne. */
  gravity: number;
}

export type SpeedResult = 'running' | 'braking' | 'done';

/** Speed allowed while collision ahead is not loaded (m/s). */
export const SPEED_UNREADY = 30;
/** A drop this much deeper than a walkable descent is a ledge to stop before (m). */
export const LEDGE_HOP = 1;
/** Ground steeper than the slope limit counts as a slope to stop before once it rises this high (m): lower ones are stepped up. */
const STEP_UP = 0.5;
/** Distance kept from an obstacle when the braking curve stops (m). */
export const STOP_MARGIN = 2;
/** Ground probes ahead along the course, this far apart (m). */
export const PROBE_STEP = 5;
/** Farthest ground probe (m). */
const PROBE_MAX = 260;
/** Ground under the runner is searched this far down (m); none: no probes (airborne high up, which brakes anyway). */
const PROBE_DEPTH = 80;
/** A probe that finds no ground in its window looks this far above it (m): ground there is a slope too steep. */
const PROBE_ABOVE = 40;
/** ...and this far below it (m): ground there is a ledge; none at all, under a point said to be loaded, is a gap in the collision (unloaded). */
const PROBE_BELOW = 4000;
/** Bisections that place a hazard between two probes (to PROBE_STEP / 256: fine enough that the curve brakes smoothly down to sprint speed). */
const BISECT = 8;

type Hazard = 'wall' | 'slope' | 'ledge' | 'unloaded';

const _t = new Vector3();
const _c = new Vector3();
const _q = new Quaternion();
const _move = new Vector3();
const _wallN = new Vector3();

export class Speed {
  speed = 0;
  /** Course (unit, tangent plane). */
  readonly course = new Vector3(0, 0, -1);
  /** Velocity of the last step (m/s). */
  readonly vel = new Vector3();
  /** Leaving: brake down to sprint speed, then hand back to walking. */
  braking = false;
  /** Vertical speed while airborne (m/s, up > 0). */
  vVert = 0;
  airTime = 0;
  /** Distance to the nearest obstacle found this step (m; Infinity = none) and why. */
  obstacle = Infinity;
  obstacleKind: Hazard | null = null;

  /** Rise or fall per metre along a slope at the limit. */
  private readonly tanMax: number;

  constructor(readonly p: SpeedParams) {
    this.tanMax = Math.tan((p.maxSlopeDeg * Math.PI) / 180);
  }

  /** Start from walking: carry the current ground speed along the heading. */
  start(vel: Vector3, s: SpeedSense): void {
    const up = s.up;
    this.course.copy(s.heading).addScaledVector(up, -s.heading.dot(up)).normalize();
    this.speed = Math.max(0, _t.copy(vel).addScaledVector(up, -vel.dot(up)).dot(this.course));
    this.braking = false;
    this.vVert = 0;
    this.airTime = 0;
  }

  /** Resume after a reload: braking from rest along the heading (a save keeps no speed); Q held resumes the run as in any braking. */
  resume(s: SpeedSense): void {
    this.start(_move.set(0, 0, 0), s);
    this.braking = true;
  }

  /** Stopping distance from a speed at the braking rate (m). */
  stopDistance(v = this.speed): number {
    return (v * v) / (2 * this.p.brake);
  }

  /** After the move: a wall the probes did not foresee took the speed it blocked; the run goes on from the speed that got through (m/s, full 3D). */
  blocked(actual: number): void {
    if (actual < this.speed - 1) this.speed = actual;
  }

  /** How far the move after a step snaps down onto the ground (m): as far as a slope at the limit falls in one step, so crests and dips are run over, not launched off. */
  snap(dt: number): number {
    return Math.max(0.6, this.speed * dt * this.tanMax);
  }

  step(dt: number, inp: SpeedInput, s: SpeedSense): SpeedResult {
    const p = this.p;
    const up = s.up;
    // Steering: the course turns toward the heading, slower at speed.
    const yawRate = p.yawLow + (p.yawHigh - p.yawLow) * Math.min(1, this.speed / p.top);
    this.course.addScaledVector(up, -this.course.dot(up)).normalize();
    _t.copy(s.heading).addScaledVector(up, -s.heading.dot(up));
    if (_t.lengthSq() > 1e-8) {
      _t.normalize();
      const ang = Math.atan2(_c.crossVectors(this.course, _t).dot(up), this.course.dot(_t));
      const turn = Math.max(-yawRate * dt, Math.min(yawRate * dt, ang));
      if (turn !== 0) this.course.applyQuaternion(_q.setFromAxisAngle(up, turn)).normalize();
    }
    // Leaving always brakes; Q held again resumes the run.
    if (!inp.run || inp.brake) this.braking = true;
    else if (this.braking && inp.run && !inp.brake) this.braking = false;
    if (!s.grounded) {
      this.airTime += dt;
      // Airborne for long (off a bump or ledge): brake.
      if (this.airTime > 0.4) this.braking = true;
    } else this.airTime = 0;
    this.speed = this.braking ? Math.max(0, this.speed - p.brake * dt) : Math.min(p.top, this.speed + p.accel * dt);

    // Direction of travel along the ground (projected onto its plane).
    _move.copy(this.course);
    if (s.grounded && s.normal) {
      _move.addScaledVector(s.normal, -_move.dot(s.normal));
      if (_move.lengthSq() > 1e-8) _move.normalize();
      else _move.copy(this.course);
    }
    // Obstacles ahead, within the stopping distance plus margins: walls by a
    // capsule sweep along the ground (a rise no steeper than the slope limit
    // is no wall: the controller runs up it), slopes, ledges and unloaded
    // collision by ground probes every PROBE_STEP along the course. Each probe
    // searches within a walkable slope of the ground before it, so long
    // rises and descents are followed. The first hazard is placed between
    // its probes by bisection, so its distance shrinks continuously as the
    // runner closes in and the curve brakes at the brake rate. (Probe
    // distances are horizontal: on a slope the path is longer, so the stop
    // comes early rather than late.)
    const reach = this.stopDistance(Math.max(this.speed, 1)) + this.speed * dt * 2 + STOP_MARGIN + 5;
    this.obstacle = Infinity;
    this.obstacleKind = null;
    const wall = s.clear(_move, reach, _wallN);
    if (Number.isFinite(wall) && _wallN.dot(up) < Math.cos((p.maxSlopeDeg * Math.PI) / 180)) this.note(wall, 'wall');
    // From the ground under the runner (in the air over a descent it is rightly below the feet).
    const base = s.ground(this.course, 0, 0.5, -PROBE_DEPTH);
    if (base) {
      let prevD = 0;
      let dRef = 0;
      let hRef = base.h;
      const far = Math.min(reach * 1.25, PROBE_MAX);
      for (let d = PROBE_STEP; d <= far + 1e-9; d += PROBE_STEP) {
        const k = this.hazard(s, hRef, d - dRef, d);
        if (k.kind) {
          this.locate(s, prevD, hRef, d - dRef, d, k.kind);
          break;
        }
        prevD = d;
        // Steep ground within a step or a hop is run over, but heights are
        // judged from walkable ground only (the allowance must not compound
        // down a steep face).
        if (!k.steep) {
          dRef = d;
          hRef = k.h;
        }
      }
    }
    // The braking curve: never faster than what can stop before the obstacle.
    // Where collision ahead is merely not loaded yet, limited but never
    // stalled (charter J).
    if (Number.isFinite(this.obstacle)) {
      const room = Math.max(0, this.obstacle - STOP_MARGIN - this.speed * dt);
      let cap = Math.sqrt(2 * p.brake * room);
      if (this.obstacleKind === 'unloaded') cap = Math.max(cap, SPEED_UNREADY);
      this.speed = Math.min(this.speed, cap);
    }

    // Velocity: along the ground (a landing ends the fall), gravity in the air.
    if (s.grounded && s.normal) this.vVert = 0;
    else this.vVert -= s.gravity * dt;
    this.vel.copy(_move).multiplyScalar(this.speed);
    if (!s.grounded) this.vel.addScaledVector(up, this.vVert);
    if (this.braking && this.speed <= SPEED_EXIT_MAX && s.grounded) return 'done';
    return this.braking ? 'braking' : 'running';
  }

  /**
   * What the ground `d` metres ahead along the course is, judged from the
   * height `hRef` of the last walkable probe, `span` metres behind the probe
   * that is judged: it must lie within a walkable slope over that span of it
   * (with a step up or a hop down), and where it is steeper than the limit
   * it may rise or fall only by that step or hop. Between two probes every
   * point is judged as the farther probe was, so where a hazard is placed
   * does not depend on where the probes happen to fall as the runner moves.
   */
  private hazard(s: SpeedSense, hRef: number, span: number, d: number): { kind: Hazard | null; h: number; steep: boolean } {
    if (!s.ready(d)) return { kind: 'unloaded', h: hRef, steep: false };
    const top = hRef + span * this.tanMax + STEP_UP;
    const bottom = hRef - span * this.tanMax - LEDGE_HOP;
    const g = s.ground(this.course, d, top, bottom);
    if (!g) {
      // Ground above the window is too steep a slope, below it a ledge; none
      // at all (a strip past the edge of the last loaded tile) is unloaded.
      const kind = s.ground(this.course, d, top + PROBE_ABOVE, top) ? 'slope' : s.ground(this.course, d, bottom, bottom - PROBE_BELOW) ? 'ledge' : 'unloaded';
      return { kind, h: hRef, steep: false };
    }
    const steep = g.slopeDeg > this.p.maxSlopeDeg;
    if (steep && g.h - hRef > STEP_UP) return { kind: 'slope', h: g.h, steep };
    if (steep && hRef - g.h > LEDGE_HOP) return { kind: 'ledge', h: g.h, steep };
    return { kind: null, h: g.h, steep };
  }

  /** Place a hazard found between a good probe (lo) and a bad one (hi) by bisection, every point judged as hi was; noted at the last good point. */
  private locate(s: SpeedSense, lo: number, hRef: number, span: number, hi: number, kind: Hazard): void {
    for (let i = 0; i < BISECT; i++) {
      const mid = (lo + hi) / 2;
      const k = this.hazard(s, hRef, span, mid);
      if (k.kind) {
        hi = mid;
        kind = k.kind;
      } else lo = mid;
    }
    this.note(lo, kind);
  }

  private note(d: number, kind: Hazard): void {
    if (d < this.obstacle) {
      this.obstacle = d;
      this.obstacleKind = kind;
    }
  }
}
