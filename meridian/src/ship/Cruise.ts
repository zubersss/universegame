import { Quaternion, Vector3 } from 'three';
import { CRUISE } from '../game/config';
import { raySphere, segmentSphereEnter } from '../core/mathx';
import { BODIES, BODY_IDS, type BodyDef, type BodyId } from '../world/bodies';

// Interplanetary cruise: an explicit assisted travel mode. While cruising the
// cruise controller is the only owner of the ship transform; it integrates the
// double-precision system position with the fixed timestep (Rapier does not
// advance the ship). Every step sweeps the travel segment against all bodies'
// expanded safety spheres with an exact segment/sphere test, and the speed is
// limited so the ship can always stop before the nearest envelope ahead.

/** Safety-envelope radius of a body: surface + atmosphere + fixed margin. */
export function safetyRadius(def: BodyDef): number {
  return def.radius + def.atmosphereHeight + CRUISE.envelopeMargin;
}

/** Distance along a unit direction to the first safety envelope it enters (Infinity if none). */
export function freeDistance(pos: Vector3, dir: Vector3): { distance: number; body: BodyId | null } {
  let best = Infinity;
  let body: BodyId | null = null;
  for (const id of BODY_IDS) {
    const b = BODIES[id];
    const hit = raySphere(pos.x, pos.y, pos.z, dir.x, dir.y, dir.z, b.center[0], b.center[1], b.center[2], safetyRadius(b));
    if (!hit) continue;
    const [t0, t1] = hit;
    if (t1 < 0) continue; // behind
    const t = Math.max(t0, 0);
    if (t < best) {
      best = t;
      body = id;
    }
  }
  return { distance: best, body };
}

/** The body whose envelope contains `pos`, or null when outside every envelope. */
export function insideEnvelope(pos: Vector3): BodyId | null {
  for (const id of BODY_IDS) {
    const b = BODIES[id];
    const dx = pos.x - b.center[0], dy = pos.y - b.center[1], dz = pos.z - b.center[2];
    if (dx * dx + dy * dy + dz * dz < safetyRadius(b) ** 2) return id;
  }
  return null;
}

export type CruiseExitReason = 'approach' | 'brake' | 'toggle' | 'safety';

export interface CruiseInput {
  /** Turn commands -1..1 (scaled to the cruise turn rate). */
  pitch: number;
  yaw: number;
  roll: number;
  /** Throttle 0..1 sets the target cruise speed. */
  throttle: number;
  brake: boolean;
  /** Edge-triggered request to leave cruise. */
  toggleOff: boolean;
}

export interface CruiseStepResult {
  /** Set when cruise ended this step (the ship hands back to normal flight). */
  exit: CruiseExitReason | null;
}

const _fwd = new Vector3();
const _p1 = new Vector3();
const _c = new Vector3();
const _q = new Quaternion();
const _axis = new Vector3();
const _cand = new Quaternion();
const _cf = new Vector3();

/**
 * Cruise state for one ship. `pos` is the authoritative system position
 * (doubles), `quat` the ship orientation, `speed` the scalar cruise speed
 * along the ship's forward axis (-Z).
 */
export class CruiseController {
  readonly pos = new Vector3();
  readonly quat = new Quaternion();
  speed = 0;
  /** Leaving cruise: decelerating toward the exit speed. */
  exiting: CruiseExitReason | null = null;
  /** Free distance ahead (m) and the body it belongs to, from the last step. */
  ahead = Infinity;
  aheadBody: BodyId | null = null;
  /** True while the speed is being limited by an envelope ahead. */
  limited = false;
  /** Turns refused because they would point the ship into an envelope it cannot stop for. */
  refusedTurns = 0;
  /** Steps in which the exact segment test had to stop the ship (must stay 0). */
  safetyStops = 0;

  /** Whether cruise may begin here: outside all envelopes with clear stopping distance ahead. */
  static canEngage(pos: Vector3, quat: Quaternion, speed: number): { ok: boolean; reason: string | null } {
    const inside = insideEnvelope(pos);
    if (inside) {
      const b = BODIES[inside];
      const need = safetyRadius(b) - b.radius;
      return { ok: false, reason: `Too close to ${b.name}: climb above ${(need / 1000).toFixed(0)} km altitude.` };
    }
    _fwd.set(0, 0, -1).applyQuaternion(quat);
    const { distance, body } = freeDistance(pos, _fwd);
    const need = (speed * speed) / (2 * CRUISE.accel) + CRUISE.safetyMargin + 5000;
    if (distance < need) {
      return { ok: false, reason: `${BODIES[body!].name} is directly ahead: turn away to engage cruise.` };
    }
    return { ok: true, reason: null };
  }

  begin(pos: Vector3, quat: Quaternion, velocity: Vector3): void {
    this.pos.copy(pos);
    this.quat.copy(quat).normalize();
    _fwd.set(0, 0, -1).applyQuaternion(this.quat);
    this.speed = Math.max(0, velocity.dot(_fwd));
    this.exiting = null;
    this.limited = false;
  }

  /** Current velocity vector (system frame). */
  velocity(out: Vector3): Vector3 {
    return out.set(0, 0, -1).applyQuaternion(this.quat).multiplyScalar(this.speed);
  }

  /** Allowed speed so that the ship can stop `margin` short of the envelope `d` ahead. */
  private static allowed(d: number): number {
    const room = d - CRUISE.safetyMargin;
    return room > 0 ? Math.sqrt(2 * CRUISE.accel * room) : 0;
  }

  step(dt: number, input: CruiseInput): CruiseStepResult {
    // Exit requests decelerate to the hand-over speed rather than stopping instantly.
    if (!this.exiting && input.brake) this.exiting = 'brake';
    if (!this.exiting && input.toggleOff) this.exiting = 'toggle';

    // Turning, limited to the cruise turn rate; refuse turns into an envelope we cannot stop for.
    // The pitch/yaw command is limited as a vector so the heading never turns
    // faster than the cruise turn rate; roll does not change the heading.
    const rate = CRUISE.turnRate;
    const pm = Math.hypot(input.pitch, input.yaw);
    const k = pm > 1 ? 1 / pm : 1;
    const wx = input.pitch * k * rate;
    const wy = -input.yaw * k * rate;
    const wz = -input.roll * rate * 3;
    const w = Math.sqrt(wx * wx + wy * wy + wz * wz);
    if (w > 1e-9) {
      _axis.set(wx / w, wy / w, wz / w);
      _q.setFromAxisAngle(_axis, w * dt);
      _cand.copy(this.quat).multiply(_q).normalize();
      _cf.set(0, 0, -1).applyQuaternion(_cand);
      const before = freeDistance(this.pos, _fwd.set(0, 0, -1).applyQuaternion(this.quat)).distance;
      const after = freeDistance(this.pos, _cf).distance;
      const need = (this.speed * this.speed) / (2 * CRUISE.accel) + CRUISE.safetyMargin + this.speed * dt;
      if (after < need && after < before) this.refusedTurns++;
      else this.quat.copy(_cand);
    }

    _fwd.set(0, 0, -1).applyQuaternion(this.quat);
    const fd = freeDistance(this.pos, _fwd);
    this.ahead = fd.distance;
    this.aheadBody = fd.body;
    let target = this.exiting ? CRUISE.exitSpeed : Math.max(0, Math.min(1, input.throttle)) * CRUISE.maxSpeed;
    const allow = CruiseController.allowed(fd.distance - this.speed * dt);
    this.limited = allow < target;
    if (this.limited) target = allow;
    const dv = CRUISE.accel * dt;
    this.speed = this.speed < target ? Math.min(target, this.speed + dv) : Math.max(target, this.speed - dv);

    // Hand back to normal flight once slow enough near an envelope, or when an exit was requested.
    const nearEnvelope = fd.distance - CRUISE.safetyMargin < (CRUISE.exitSpeed * CRUISE.exitSpeed) / (2 * CRUISE.accel) + CRUISE.exitSpeed * 2;
    let exit: CruiseExitReason | null = null;
    if (this.speed <= CRUISE.exitSpeed + 1e-6) {
      if (this.exiting) exit = this.exiting;
      else if (nearEnvelope) exit = 'approach';
    }

    // Integrate the system position with an exact segment/sphere sweep.
    _p1.copy(this.pos).addScaledVector(_fwd, this.speed * dt);
    for (const id of BODY_IDS) {
      const b = BODIES[id];
      _c.set(b.center[0], b.center[1], b.center[2]);
      const t = segmentSphereEnter(this.pos, _p1, _c, safetyRadius(b));
      if (t >= 0) {
        // Never cross an envelope: stop short and hand back to normal flight.
        _p1.lerpVectors(this.pos, _p1, Math.max(0, t - 1e-6));
        this.speed = Math.min(this.speed, CRUISE.exitSpeed);
        this.safetyStops++;
        exit = 'safety';
      }
    }
    this.pos.copy(_p1);
    if (exit) this.exiting = null;
    return { exit };
  }
}
