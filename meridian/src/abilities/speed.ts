import { Quaternion, Vector3 } from 'three';
import { SPEED_EXIT_MAX, type SpeedParams } from './types';

// The speed primitive (Redline; Sunline Dash is a burst variant). Charter K:
// hold Q while grounded to run, steer with the look (yaw rate falls from
// 3 to 0.8 rad/s with speed), X or releasing Q brakes. Charter J: every
// step the path ahead is checked (swept capsule for walls, ground probes for
// slopes steeper than the limit and for ledges), and the speed never exceeds
// what the braking curve can stop before the nearest such obstacle; where
// collision ahead is not loaded the speed is limited instead of stalling.
// Leaving superspeed always passes through braking down to sprint speed.

export interface SpeedInput {
  /** Q held. */
  run: boolean;
  /** X held. */
  brake: boolean;
}

/** Ground found ahead along the course: height relative to the feet (m) and slope (deg). */
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
  /** Free distance along a direction for the walker's capsule lifted above the ground (Infinity when clear). */
  clear(dir: Vector3, dist: number): number;
  /** Ground `ahead` metres along the course, or null when there is none within reach (a drop or unloaded). */
  groundAhead(dir: Vector3, ahead: number): GroundAhead | null;
  /** Collision is loaded `dist` metres along the course (charter J readiness). */
  ready(dist: number): boolean;
  /** Gravity (m/s^2) while airborne. */
  gravity: number;
}

export type SpeedResult = 'running' | 'braking' | 'done';

/** Speed allowed while collision ahead is not loaded (m/s). */
export const SPEED_UNREADY = 30;
/** A drop deeper than this between probes ahead is a ledge to stop before (m). */
export const LEDGE_DROP = 4;
/** Distance kept from an obstacle when the braking curve stops (m). */
export const STOP_MARGIN = 2;
/** Probe distances ahead (m), scaled up to the stopping distance. */
const PROBES = [2, 4, 8, 16, 32, 64, 128, 256];

const _t = new Vector3();
const _c = new Vector3();
const _q = new Quaternion();
const _move = new Vector3();

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
  obstacleKind: 'wall' | 'slope' | 'ledge' | 'unloaded' | null = null;

  constructor(readonly p: SpeedParams) {}

  /** Start from walking: carry the current ground speed along the heading. */
  start(vel: Vector3, s: SpeedSense): void {
    const up = s.up;
    this.course.copy(s.heading).addScaledVector(up, -s.heading.dot(up)).normalize();
    this.speed = Math.max(0, _t.copy(vel).addScaledVector(up, -vel.dot(up)).dot(this.course));
    this.braking = false;
    this.vVert = 0;
    this.airTime = 0;
  }

  /** Stopping distance from a speed at the braking rate (m). */
  stopDistance(v = this.speed): number {
    return (v * v) / (2 * this.p.brake);
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
    // capsule sweep along the ground, slopes and ledges by probes.
    const reach = this.stopDistance(Math.max(this.speed, 1)) + this.speed * dt * 2 + STOP_MARGIN + 5;
    this.obstacle = Infinity;
    this.obstacleKind = null;
    const wall = s.clear(_move, Math.min(reach, this.speed * 0.6 + 6));
    if (Number.isFinite(wall)) this.note(wall, 'wall');
    let prevH = 0;
    for (const d of PROBES) {
      if (d > reach * 1.25 && d > PROBES[0]) break;
      const g = s.groundAhead(this.course, d);
      if (!g) {
        this.note(d, s.ready(d) ? 'ledge' : 'unloaded');
        break;
      }
      if (g.h > prevH && g.slopeDeg > p.maxSlopeDeg) {
        this.note(d, 'slope');
        break;
      }
      if (prevH - g.h > LEDGE_DROP) {
        this.note(d, 'ledge');
        break;
      }
      prevH = g.h;
    }
    // The braking curve: never faster than what can stop before the obstacle.
    if (Number.isFinite(this.obstacle)) {
      const room = Math.max(0, this.obstacle - STOP_MARGIN - this.speed * dt);
      this.speed = Math.min(this.speed, Math.sqrt(2 * p.brake * room));
    }
    if (!s.ready(p.lookaheadTime * this.speed + p.lookaheadMargin)) this.speed = Math.min(this.speed, SPEED_UNREADY);

    // Velocity: along the ground, gravity in the air.
    if (s.grounded && s.normal) this.vVert = Math.min(0, this.vVert);
    else this.vVert -= s.gravity * dt;
    this.vel.copy(_move).multiplyScalar(this.speed);
    if (!s.grounded) this.vel.addScaledVector(up, this.vVert);
    if (this.braking && this.speed <= SPEED_EXIT_MAX && s.grounded) return 'done';
    return this.braking ? 'braking' : 'running';
  }

  private note(d: number, kind: 'wall' | 'slope' | 'ledge' | 'unloaded'): void {
    if (d < this.obstacle) {
      this.obstacle = d;
      this.obstacleKind = kind;
    }
  }
}
