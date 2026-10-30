import { Quaternion, Vector3 } from 'three';
import type { FlightParams } from './types';

// The flight primitive (Skyborne Flight; Pressure Glide and Wing Glide are
// parameter variants). Charter K controls: hold Space to take off, Space /
// Ctrl climb / descend, W / S speed up / slow down, Shift boost, X brake to a
// hover, descend slowly near the ground to land. The flier keeps a forward
// speed setpoint along a horizontal course that turns toward the camera's
// heading at a limited rate; vertical speed follows Space / Ctrl; the
// velocity approaches its target within the acceleration limits. No gravity
// while flying (powered hover). Flight never ends in the air: it ends only by
// landing (near the ground, slow, not climbing).

/** Controls sampled each fixed step. */
export interface FlightInput {
  climb: boolean;
  descend: boolean;
  faster: boolean;
  slower: boolean;
  boost: boolean;
  brake: boolean;
}

/** What flight reads about the flier and the world each step. */
export interface FlightSense {
  /** Radial up. */
  up: Vector3;
  /** Camera heading (tangent plane): the course turns toward it. */
  heading: Vector3;
  /** Height of the feet above the ground below (m), null when unknown (collision not loaded). */
  height: number | null;
  /** Whether the character controller reports ground contact. */
  grounded: boolean;
  /** The ground below is walkable (no steeper than the walking limit): flight lands only there. */
  walkable: boolean;
  /**
   * How far along the path collision is loaded (m; Infinity: as far as was
   * probed). Charter J readiness: never faster than what can brake to a stop
   * inside it, and never slower than FLIGHT_UNREADY_SPEED (limited, not stalled).
   */
  loaded: number;
}

export type FlightResult = 'flying' | 'landed';

/** Speed allowed while collision ahead is not loaded (m/s). */
export const FLIGHT_UNREADY_SPEED = 25;
/** Distance kept between a stop and the end of loaded collision (m). */
export const FLIGHT_LOAD_MARGIN = 30;
/** Descent while settling onto the ground to land (m/s). */
export const FLIGHT_SETTLE = 1.5;
/** Height a flier that is not landing keeps above the ground (m). */
export const FLIGHT_SKIM = 0.6;
/** Upward speed at take-off (m/s). */
export const FLIGHT_TAKEOFF_CLIMB = 6;

const _t = new Vector3();
const _q = new Quaternion();
const _target = new Vector3();
const _c = new Vector3();

export class Flight {
  /** Forward speed setpoint (m/s). */
  speed = 0;
  /** Horizontal course (unit, tangent plane). */
  readonly course = new Vector3(0, 0, -1);
  /** Current velocity (m/s, full 3D). */
  readonly vel = new Vector3();
  /** Seconds since take-off (landing is ignored briefly after take-off). */
  time = 0;
  /** Speed allowed by the loaded collision ahead this step (m/s; Infinity: no limit). */
  limit = Infinity;

  constructor(readonly p: FlightParams) {}

  /**
   * Take off: course along the heading, carrying the current velocity. Near
   * the ground (standing, or mid-jump) it kicks upward; higher up (a fall
   * caught in the air) the velocity is kept and turned around within the
   * acceleration limits instead of reversing at once.
   */
  start(vel: Vector3, sense: FlightSense): void {
    const up = sense.up;
    this.course.copy(sense.heading).addScaledVector(up, -sense.heading.dot(up)).normalize();
    this.vel.copy(vel);
    const h = _t.copy(vel).addScaledVector(up, -vel.dot(up));
    this.speed = Math.max(0, h.dot(this.course));
    const vz = vel.dot(up);
    const low = sense.grounded || (sense.height !== null && sense.height < this.p.landHeight);
    if (low && vz < FLIGHT_TAKEOFF_CLIMB) this.vel.addScaledVector(up, FLIGHT_TAKEOFF_CLIMB - vz);
    this.time = 0;
  }

  /** Resume after a reload: hovering in place along the heading (a save keeps no velocity); no take-off climb, so landing is allowed at once. */
  resume(sense: FlightSense): void {
    const up = sense.up;
    this.course.copy(sense.heading).addScaledVector(up, -sense.heading.dot(up)).normalize();
    this.vel.set(0, 0, 0);
    this.speed = 0;
    this.time = 1;
  }

  /** One fixed step: returns the new velocity in `this.vel` and whether flight continues. */
  step(dt: number, inp: FlightInput, s: FlightSense): FlightResult {
    const p = this.p;
    const up = s.up;
    this.time += dt;
    // Course: turn toward the heading at most `turn` rad/s (kept in the tangent plane).
    this.course.addScaledVector(up, -this.course.dot(up)).normalize();
    _t.copy(s.heading).addScaledVector(up, -s.heading.dot(up));
    if (_t.lengthSq() > 1e-8) {
      _t.normalize();
      const ang = Math.atan2(_c.crossVectors(this.course, _t).dot(up), this.course.dot(_t));
      const turn = Math.max(-p.turn * dt, Math.min(p.turn * dt, ang));
      if (turn !== 0) this.course.applyQuaternion(_q.setFromAxisAngle(up, turn)).normalize();
    }
    // Speed setpoint: W / S at the acceleration; Shift holds boost; above
    // cruise without boost it settles back at the acceleration; X brakes.
    if (inp.brake) this.speed = Math.max(0, this.speed - p.brake * dt);
    else {
      if (inp.faster) this.speed += p.accel * dt;
      if (inp.slower) this.speed -= p.accel * dt;
      const cap = inp.boost ? p.boost : p.cruise;
      if (inp.boost && inp.faster) this.speed = Math.min(p.boost, this.speed);
      else if (this.speed > cap) this.speed = Math.max(cap, this.speed - p.accel * dt);
      this.speed = Math.max(0, this.speed);
    }
    // Readiness governs the speed flown, not the chosen setpoint: when loading
    // catches up the flier returns to the speed the player chose.
    this.limit = Number.isFinite(s.loaded) ? Math.max(FLIGHT_UNREADY_SPEED, Math.sqrt(2 * p.brake * Math.max(0, s.loaded - FLIGHT_LOAD_MARGIN))) : Infinity;
    const forward = Math.min(this.speed, this.limit);
    // Vertical target: climb / descend / hold (hover), braked by X, capped near the ceiling.
    let vz = inp.brake ? 0 : inp.climb ? p.climb : inp.descend ? -p.climb : 0;
    if (s.height !== null && s.height > p.ceiling) vz = Math.min(vz, -Math.min(p.climb, s.height - p.ceiling));
    // Landing (charter K: below the landing height and slower than the landing
    // speed, not climbing): over walkable ground the flier settles down and
    // hands back only on touchdown, never in the air and never on a cliff face.
    const settling = this.time > 0.5 && !inp.climb && this.vel.length() < p.landSpeed && s.walkable && (s.grounded || (s.height !== null && s.height < p.landHeight));
    if (settling) vz = Math.min(vz, -FLIGHT_SETTLE);
    // Near walkable ground: landing, the descent slows so it arrives slowly
    // enough to land; otherwise the flier holds FLIGHT_SKIM above it and
    // follows the terrain. Pressed into the ground it would count as standing
    // on it, and a rise steeper than the walking limit would then stop it
    // dead; met in the air, any slope is slid along. (Beside a cliff the ray
    // finds the face, which is no ground to keep clear of.)
    if (s.height !== null && s.walkable) {
      if (settling) {
        if (vz < 0) vz = Math.max(vz, -(0.6 * p.landSpeed + 1.2 * s.height));
      } else vz = Math.max(vz, -1.2 * (s.height - FLIGHT_SKIM));
    }
    // Velocity toward the target within the acceleration (brake rate when
    // braking), across and along up separately: a push against a wall that
    // the controller blocks does not hold back the climb or descent.
    _target.copy(this.course).multiplyScalar(forward).addScaledVector(up, vz);
    _t.copy(_target).sub(this.vel);
    const dz = _t.dot(up);
    _t.addScaledVector(up, -dz);
    const across = (inp.brake ? p.brake : Math.max(p.accel, p.climb * 2)) * dt;
    const along = (inp.brake ? p.brake : p.climb * 2) * dt;
    const dh = _t.length();
    if (dh > across) _t.multiplyScalar(across / dh);
    this.vel.add(_t).addScaledVector(up, Math.max(-along, Math.min(along, dz)));
    if (settling && s.grounded && this.vel.dot(up) <= 0.1) return 'landed';
    return 'flying';
  }
}
