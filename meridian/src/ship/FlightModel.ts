import { Quaternion, Vector3 } from 'three';
import { FLIGHT } from '../game/config';
import { clamp, lerp, smoothstep } from '../core/mathx';
import type { BodyDef } from '../world/bodies';

export interface ShipControls {
  /** -1..1, positive = nose up. */
  pitch: number;
  /** -1..1, positive = yaw right. */
  yaw: number;
  /** -1..1, positive = roll right. */
  roll: number;
  /** -1..1 throttle change request (W = +1, S = -1). */
  throttleAxis: number;
  /** -1..1 (Space = ascend, Ctrl = descend). */
  vertical: number;
  boost: boolean;
  brake: boolean;
}

export const NO_CONTROLS: ShipControls = { pitch: 0, yaw: 0, roll: 0, throttleAxis: 0, vertical: 0, boost: false, brake: false };

export interface FlightEnv {
  body: BodyDef;
  /** Local gravity acceleration at the ship. */
  gravity: Vector3;
  /** Radial up at the ship (unit). */
  up: Vector3;
  /** Height above the body's datum radius. */
  altitude: number;
  /** Height above the actual terrain surface. */
  clearance: number;
  /** Normalized air density 0..1. */
  density: number;
  /** True when within a few radii of the body: vertical control is radial. */
  nearBody: boolean;
  /** Speed limit imposed by terrain/collision readiness (Infinity if none). */
  terrainSpeedLimit: number;
  /** Probe clearance/density at a point along the path (local coordinates). */
  probe(localX: number, localY: number, localZ: number): { clearance: number; density: number };
}

export interface ShipState {
  pos: Vector3; // local
  vel: Vector3;
  quat: Quaternion;
  angvel: Vector3; // world
}

export interface FlightOutput {
  /** Net force to apply this step (N, world frame). */
  force: Vector3;
  /** New angular velocity (rad/s, world frame). */
  angvel: Vector3;
}

/** Overrides used by landing assist (target velocity/orientation supplied externally). */
export interface FlightOverride {
  vTarget: Vector3;
  tau: number;
  aMax: number;
  /** Desired body-local angular velocity (already including alignment). */
  angTargetLocal: Vector3;
}

const _fwd = new Vector3();
const _right = new Vector3();
const _vt = new Vector3();
const _a = new Vector3();
const _drag = new Vector3();
const _qi = new Quaternion();
const _wl = new Vector3();
const _wt = new Vector3();
const _dir = new Vector3();
const _vertDir = new Vector3();

/** "Space factor": 0 in the lower atmosphere / near the ground, 1 in open space. */
export function spaceFactor(body: BodyDef, altitude: number, clearance: number): number {
  if (body.atmosphere) return smoothstep(body.atmosphereHeight * 0.85, body.atmosphereHeight * 1.25, altitude);
  return smoothstep(800, 3000, clearance);
}

/** Local speed cap for a given clearance/density situation. */
export function speedCapAt(body: BodyDef, altitude: number, clearance: number, boost: boolean): number {
  const lowBlend = smoothstep(FLIGHT.lowClearance, FLIGHT.atmoBlendClearance, clearance);
  const atmoBoost = boost && clearance > FLIGHT.boostMinClearance;
  const atmoCap = lerp(FLIGHT.capLow, atmoBoost ? FLIGHT.capAtmoBoost : FLIGHT.capAtmo, lowBlend);
  const spaceCap = boost ? FLIGHT.capSpaceBoost : FLIGHT.capSpace;
  return lerp(atmoCap, spaceCap, spaceFactor(body, altitude, clearance));
}

export class FlightModel {
  /** Target throttle 0..1 (fraction of the current speed cap). */
  throttle = 0;
  /** Last computed effective speed cap (m/s). */
  speedCap: number = FLIGHT.capLow;
  /** Thrust acceleration (world) from the last step, for effects. */
  readonly thrustAccel = new Vector3();
  /** Forward component of thrust acceleration (m/s^2), for engine effects. */
  forwardThrust = 0;
  boostActive = false;
  braking = false;

  reset(): void {
    this.throttle = 0;
    this.thrustAccel.set(0, 0, 0);
    this.forwardThrust = 0;
  }

  /**
   * Compute the cap at the ship, then reduce it so the ship can slow to the
   * cap found at points ahead along its path (no instant clamp at boundaries).
   */
  effectiveCap(s: ShipState, env: FlightEnv, boost: boolean, decel: number): number {
    let cap = speedCapAt(env.body, env.altitude, env.clearance, boost);
    const speed = s.vel.length();
    if (speed > 1) {
      _dir.copy(s.vel).divideScalar(speed);
      const stop = (speed * speed) / (2 * decel);
      for (const f of [0.25, 0.5, 1, 1.6]) {
        const d = stop * f + 50;
        const p = env.probe(s.pos.x + _dir.x * d, s.pos.y + _dir.y * d, s.pos.z + _dir.z * d);
        const alt = env.altitude + (p.clearance - env.clearance);
        const capAhead = speedCapAt(env.body, alt, p.clearance, boost);
        cap = Math.min(cap, Math.sqrt(capAhead * capAhead + 2 * decel * d));
      }
    }
    return Math.min(cap, env.terrainSpeedLimit);
  }

  step(dt: number, s: ShipState, c: ShipControls, env: FlightEnv, out: FlightOutput, override?: FlightOverride): void {
    const sf = spaceFactor(env.body, env.altitude, env.clearance);
    const atmo = 1 - sf;
    // Throttle.
    this.throttle = clamp(this.throttle + c.throttleAxis * FLIGHT.throttleRate * dt, 0, 1);
    if (c.brake) this.throttle = 0;
    this.braking = c.brake;
    const boostAllowed = c.boost && (sf > 0.5 || env.clearance > FLIGHT.boostMinClearance);
    this.boostActive = boostAllowed && !c.brake;

    const aMaxNormal = lerp(FLIGHT.accelSpace, FLIGHT.accelAtmo, atmo);
    const aBrake = lerp(FLIGHT.brakeSpace, FLIGHT.brakeAtmo, atmo);
    let tau = lerp(FLIGHT.tauSpace, FLIGHT.tauAtmo, atmo);
    let aMax = aMaxNormal;

    _fwd.set(0, 0, -1).applyQuaternion(s.quat);
    if (override) {
      _vt.copy(override.vTarget);
      tau = override.tau;
      aMax = override.aMax;
      this.speedCap = _vt.length();
    } else if (c.brake) {
      _vt.set(0, 0, 0);
      tau = FLIGHT.tauBrake;
      aMax = aBrake;
      this.speedCap = 0;
    } else {
      const cap = this.effectiveCap(s, env, this.boostActive, aMaxNormal * 0.8);
      this.speedCap = cap;
      _vt.copy(_fwd).multiplyScalar(this.throttle * cap);
      // Vertical control: radial near a body, ship-relative in open space.
      if (env.nearBody) _vertDir.copy(env.up);
      else _vertDir.set(0, 1, 0).applyQuaternion(s.quat);
      const lowV = lerp(FLIGHT.verticalSpeedLow, FLIGHT.verticalSpeedAtmo, smoothstep(FLIGHT.lowClearance, FLIGHT.atmoBlendClearance, env.clearance));
      const vSpeed = lerp(lowV, FLIGHT.verticalSpeedSpace, sf);
      _vt.addScaledVector(_vertDir, c.vertical * vSpeed);
      const l = _vt.length();
      if (l > cap) _vt.multiplyScalar(cap / l);
      // When over the cap (e.g. after entering a slower band) slow at the normal rate.
    }

    // aThrust = limit((vTarget - v)/tau - g, aMax), with the hover (gravity)
    // share allocated first so saturated acceleration never sinks the ship.
    _a.copy(_vt).sub(s.vel).divideScalar(tau);
    const gMag = env.gravity.length();
    const budget = Math.max(aMax - gMag, aMax * 0.25);
    const al = _a.length();
    if (al > budget) _a.multiplyScalar(budget / al);
    _a.sub(env.gravity);
    this.thrustAccel.copy(_a);
    this.forwardThrust = Math.max(0, _a.dot(_fwd));

    // aDrag = -density * (k1 v + k2 |v| v)
    const speed = s.vel.length();
    _drag.copy(s.vel).multiplyScalar(-env.density * (FLIGHT.k1 + FLIGHT.k2 * speed));

    // force = m (aThrust + g + aDrag)
    out.force.copy(_a).add(env.gravity).add(_drag).multiplyScalar(FLIGHT.mass);

    // ---- angular control: smooth body-local rates toward commanded rates
    _qi.copy(s.quat).invert();
    _wl.copy(s.angvel).applyQuaternion(_qi);
    if (override) {
      _wt.copy(override.angTargetLocal);
    } else {
      _wt.set(c.pitch * FLIGHT.pitchRate, -c.yaw * FLIGHT.yawRate, -c.roll * FLIGHT.rollRate);
      // Gentle auto-level of bank near a body when the pilot isn't rolling.
      if (env.nearBody && Math.abs(c.roll) < 0.05) {
        _right.set(1, 0, 0).applyQuaternion(s.quat);
        const bank = Math.asin(clamp(_right.dot(env.up), -1, 1));
        const verticality = Math.abs(_fwd.dot(env.up));
        const k = (1 - smoothstep(0.75, 0.95, verticality)) * lerp(0.35, 0.9, atmo);
        _wt.z += -bank * k;
      }
    }
    const alpha = 1 - Math.exp(-dt / FLIGHT.angTau);
    _wl.lerp(_wt, alpha);
    out.angvel.copy(_wl).applyQuaternion(s.quat);
  }
}
