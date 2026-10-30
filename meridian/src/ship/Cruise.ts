import { Quaternion, Vector3 } from 'three';
import { CRUISE } from '../game/config';
import { raySphere, segmentSphereEnter, segmentSphereExit } from '../core/mathx';
import { BODIES, BODY_IDS, SYSTEM_EXTENT, type BodyDef, type BodyId } from '../world/bodies';
import { cruiseMaxSpeed } from '../world/scale';

// Interplanetary cruise: an explicit assisted travel mode. While cruising the
// cruise controller is the only owner of the ship transform; it integrates the
// double-precision system position with the fixed timestep (Rapier does not
// advance the ship). Every step sweeps the travel segment against all bodies'
// expanded safety spheres with an exact segment/sphere test, and the speed is
// limited so the ship can always stop before the nearest envelope ahead.
// The system edge (a sphere of radius SYSTEM_EXTENT around the system origin)
// is an inside-out envelope: cruise stops before it like before a body
// (reported with body null), so it never carries a ship past what saves accept.
// The speed cap follows the hop (charter H): max(15 km/s, hop ÷ 45 s), with the
// acceleration scaled so the ramp to the cap always takes CRUISE.rampSeconds.
// The hop is the planned route length (routeHop), so a leg that bypasses the
// Sun is still one cruise of about 45 s along the nav marker's waypoints. A
// cruise restored from a save keeps a cap of at least its saved speed.
// `ids` parameters default to the bodies in play (BODY_IDS).

/** Safety-envelope radius of a body: surface + atmosphere + fixed margin; a star keeps a 5R standoff. */
export function safetyRadius(def: BodyDef): number {
  const r = def.radius + def.atmosphereHeight + CRUISE.envelopeMargin;
  return def.kind === 'star' ? Math.max(r, CRUISE.starStandoffRadii * def.radius) : r;
}

/** Hop length (m) from `pos` to a body: the straight-line distance to its safety envelope (0 inside it). */
export function hopDistance(pos: Vector3, id: BodyId): number {
  const c = BODIES[id].center;
  return Math.max(0, Math.hypot(pos.x - c[0], pos.y - c[1], pos.z - c[2]) - safetyRadius(BODIES[id]));
}

/** Distance along a unit direction to the system edge (0 at or beyond it). */
function edgeDistance(pos: Vector3, dir: Vector3): number {
  const hit = raySphere(pos.x, pos.y, pos.z, dir.x, dir.y, dir.z, 0, 0, 0, SYSTEM_EXTENT);
  return hit && hit[0] < 0 ? Math.max(hit[1], 0) : 0;
}

/** Whether `pos` is at or beyond the system edge. */
export function beyondEdge(pos: Vector3): boolean {
  return pos.lengthSq() >= SYSTEM_EXTENT * SYSTEM_EXTENT;
}

/**
 * Distance along a unit direction to the first safety envelope it enters, or
 * to the system edge (body null) when no envelope is nearer.
 */
export function freeDistance(pos: Vector3, dir: Vector3, ids: readonly BodyId[] = BODY_IDS): { distance: number; body: BodyId | null } {
  let best = edgeDistance(pos, dir);
  let body: BodyId | null = null;
  for (const id of ids) {
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
export function insideEnvelope(pos: Vector3, ids: readonly BodyId[] = BODY_IDS): BodyId | null {
  for (const id of ids) {
    const b = BODIES[id];
    const dx = pos.x - b.center[0], dy = pos.y - b.center[1], dz = pos.z - b.center[2];
    if (dx * dx + dy * dy + dz * dz < safetyRadius(b) ** 2) return id;
  }
  return null;
}

/** First body whose safety envelope, inflated by `inflate` (m), the segment a->b enters, if any. */
export function blockedBy(a: Vector3, b: Vector3, inflate: number, ids: readonly BodyId[] = BODY_IDS): BodyId | null {
  for (const id of ids) {
    const c = BODIES[id].center;
    if (segmentSphereEnter(a, b, _c.set(c[0], c[1], c[2]), safetyRadius(BODIES[id]) + inflate) >= 0) return id;
  }
  return null;
}

/** Detour points sit this far outside the blocker's inflated envelope. */
const DETOUR_CLEARANCE = 32000;

/**
 * Waypoints (system coordinates) from a to b, ending at b, whose segments stay
 * clear of every safety envelope inflated by `inflate`: a blocked segment is
 * split at a detour point outside the blocker, on the bisector of the
 * directions from its center to the segment ends (at most 5 levels deep).
 */
export function planPath(a: Vector3, b: Vector3, inflate: number, ids: readonly BodyId[] = BODY_IDS): Vector3[] {
  const split = (p: Vector3, q: Vector3, depth: number): Vector3[] => {
    const id = blockedBy(p, q, inflate, ids);
    if (!id || depth > 5) return [q.clone()];
    const cc = BODIES[id].center;
    const c = new Vector3(cc[0], cc[1], cc[2]);
    const u = p.clone().sub(c).normalize();
    const w = q.clone().sub(c).normalize();
    const m = u.clone().add(w);
    if (m.lengthSq() < 1e-6) m.set(-u.y, u.x, 0.3).cross(u);
    const detour = c.add(m.normalize().multiplyScalar(safetyRadius(BODIES[id]) + inflate + DETOUR_CLEARANCE));
    return [...split(p, detour, depth + 1), ...split(detour, q, depth + 1)];
  };
  return split(a, b, 0);
}

/**
 * Hop length (m) for a cruise from `pos` to a body: the length of the planPath
 * route around every other body's envelope (inflated by `inflate`), less the
 * destination's envelope (0 inside it). Equals hopDistance while the direct
 * line is clear; a bypass lengthens it, and with it the cap, for the whole leg.
 */
export function routeHop(pos: Vector3, id: BodyId, inflate: number, ids: readonly BodyId[] = BODY_IDS): number {
  const c = BODIES[id].center;
  const route = planPath(pos, new Vector3(c[0], c[1], c[2]), inflate, ids.filter((b) => b !== id));
  let length = 0;
  let p = pos;
  for (const q of route) {
    length += p.distanceTo(q);
    p = q;
  }
  return Math.max(0, length - safetyRadius(BODIES[id]));
}

/**
 * The hop (m) a cruise toward the nav target is capped for (begin/retarget):
 * its routeHop at CRUISE.routeInflate. 0 (the 15 km/s floor) without a target,
 * and always in the Quiet System, whose cruise keeps its fixed 15 km/s cap.
 */
export function cruiseHop(pos: Vector3, target: BodyId | null): number {
  if (!target || BODIES[target].system === 'quiet') return 0;
  return routeHop(pos, target, CRUISE.routeInflate);
}

/**
 * The cap floor (begin's minCap) for a cruise restored from a save: its saved
 * speed, which its leg's cap allowed, never above the highest cap the hop rule
 * gives any leg toward that target (the 15 km/s floor without a target or in
 * the Quiet System, as cruiseHop; else the longest hop's). The save keeps no
 * leg start (schema 2), so the leg's own hop is not recoverable.
 */
export function resumeCap(target: BodyId | null, speed: number): number {
  const top = !target || BODIES[target].system === 'quiet' ? CRUISE.maxSpeed : cruiseMaxSpeed(2 * SYSTEM_EXTENT);
  return Math.min(Math.max(0, speed), top);
}

export type CruiseExitReason = 'approach' | 'brake' | 'toggle' | 'safety';

/**
 * What one cruise leg (begin() to the hand-back) planned and reached, for the
 * cruise log. cap = the highest speed cap the leg had: cruiseMaxSpeed(hop) for
 * its longest planned hop, or for a cruise restored from a save at least its
 * saved (entry) speed, so a retarget to a nearer body (which lowers the live
 * cap) never hides a faster part of the leg. peak <= cap: a leg engaged from
 * flight enters below the 15 km/s floor, and a restored cruise keeps a cap of
 * at least its entry speed (begin's minCap).
 */
export interface CruiseLegStats {
  /** Hop (m) planned when the leg had that cap (at begin or a retarget), as capped (≤ 2·SYSTEM_EXTENT). */
  hop: number;
  /** The leg's highest speed cap (m/s). */
  cap: number;
  /** Speed at begin (m/s). */
  entry: number;
  /** Highest speed reached (m/s). */
  peak: number;
}

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
const _o = new Vector3(); // system origin (never written)
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
  /** The hop (m) the cap follows now, its speed cap (m/s) and the acceleration (m/s²) (set by begin/retarget). */
  hop = 0;
  maxSpeed: number = CRUISE.maxSpeed;
  accel: number = CRUISE.accel;
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
  /** Speed at begin() and highest speed since (m/s), and the longest hop planned since with its cap (legStats). */
  entry = 0;
  peak = 0;
  private topHop = 0;
  private topCap = 0;

  /** `ids`: the bodies this controller avoids (default: the bodies in play, read at each use). */
  constructor(private readonly ids?: readonly BodyId[]) {}

  /**
   * Whether cruise may begin here: outside all envelopes and inside the system
   * edge, with clear stopping distance ahead (at the floor acceleration, which
   * never exceeds the acceleration begin() sets).
   */
  static canEngage(pos: Vector3, quat: Quaternion, speed: number, ids: readonly BodyId[] = BODY_IDS): { ok: boolean; reason: string | null } {
    const inside = insideEnvelope(pos, ids);
    if (inside) {
      const b = BODIES[inside];
      const need = safetyRadius(b) - b.radius;
      return { ok: false, reason: `Too close to ${b.name}: climb above ${(need / 1000).toFixed(0)} km altitude.` };
    }
    if (beyondEdge(pos)) return { ok: false, reason: 'Beyond the edge of the charted system.' };
    _fwd.set(0, 0, -1).applyQuaternion(quat);
    const { distance, body } = freeDistance(pos, _fwd, ids);
    const need = (speed * speed) / (2 * CRUISE.accel) + CRUISE.safetyMargin + 5000;
    if (distance < need) {
      const what = body ? BODIES[body].name : 'The edge of the charted system';
      return { ok: false, reason: `${what} is directly ahead: turn away to engage cruise.` };
    }
    return { ok: true, reason: null };
  }

  /**
   * Start cruising; `hop` (m) is the route length to the destination's envelope
   * (routeHop; 0 = the 15 km/s floor). `minCap` (m/s) is a floor under the cap
   * for this hop (resumeCap for a cruise restored from a save, so it keeps its
   * pace instead of slowing to the remaining route's cap); a retarget drops it.
   */
  begin(pos: Vector3, quat: Quaternion, velocity: Vector3, hop = 0, minCap = 0): void {
    this.pos.copy(pos);
    this.quat.copy(quat).normalize();
    _fwd.set(0, 0, -1).applyQuaternion(this.quat);
    this.speed = Math.max(0, velocity.dot(_fwd));
    this.entry = this.peak = this.speed;
    this.topCap = 0;
    this.setHop(hop, minCap);
    this.exiting = null;
    this.limited = false;
  }

  /**
   * New destination while cruising: the cap follows the new hop (legStats
   * keeps the leg's longest hop and its cap, so a lower cap never hides the
   * speed reached before). The acceleration only drops when stopping short of
   * the envelope ahead at the lower value would still take at most half the
   * room left; otherwise the current (higher) value is kept so a braking ship
   * stays safe.
   */
  retarget(hop: number): void {
    const prev = this.accel;
    this.setHop(hop);
    if (this.accel >= prev) return;
    _fwd.set(0, 0, -1).applyQuaternion(this.quat);
    const room = freeDistance(this.pos, _fwd, this.ids).distance - CRUISE.safetyMargin;
    if (this.speed * this.speed > this.accel * room) this.accel = prev;
  }

  /** The leg so far (the cruise log entry at the hand-back). */
  legStats(): CruiseLegStats {
    return { hop: this.topHop, cap: this.topCap, entry: this.entry, peak: this.peak };
  }

  /**
   * Cap = max(15 km/s, hop ÷ 45 s, minCap), the hop clamped to [0, 2·SYSTEM_EXTENT];
   * the acceleration reaches the cap (or sheds the current speed) in rampSeconds.
   */
  private setHop(hop: number, minCap = 0): void {
    this.hop = hop > 0 ? Math.min(hop, 2 * SYSTEM_EXTENT) : 0;
    this.maxSpeed = Math.max(cruiseMaxSpeed(this.hop), minCap);
    if (this.maxSpeed > this.topCap) {
      this.topCap = this.maxSpeed;
      this.topHop = this.hop;
    }
    this.accel = Math.max(CRUISE.accel, Math.max(this.maxSpeed, this.speed) / CRUISE.rampSeconds);
  }

  /** Current velocity vector (system frame). */
  velocity(out: Vector3): Vector3 {
    return out.set(0, 0, -1).applyQuaternion(this.quat).multiplyScalar(this.speed);
  }

  /** Allowed speed so that the ship can stop `margin` short of the envelope `d` ahead. */
  private allowed(d: number): number {
    const room = d - CRUISE.safetyMargin;
    return room > 0 ? Math.sqrt(2 * this.accel * room) : 0;
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
      const before = freeDistance(this.pos, _fwd.set(0, 0, -1).applyQuaternion(this.quat), this.ids).distance;
      const after = freeDistance(this.pos, _cf, this.ids).distance;
      const need = (this.speed * this.speed) / (2 * this.accel) + CRUISE.safetyMargin + this.speed * dt;
      if (after < need && after < before) this.refusedTurns++;
      else this.quat.copy(_cand);
    }

    _fwd.set(0, 0, -1).applyQuaternion(this.quat);
    const fd = freeDistance(this.pos, _fwd, this.ids);
    this.ahead = fd.distance;
    this.aheadBody = fd.body;
    let target = this.exiting ? CRUISE.exitSpeed : Math.max(0, Math.min(1, input.throttle)) * this.maxSpeed;
    const allow = this.allowed(fd.distance - this.speed * dt);
    this.limited = allow < target;
    if (this.limited) target = allow;
    const dv = this.accel * dt;
    this.speed = this.speed < target ? Math.min(target, this.speed + dv) : Math.max(target, this.speed - dv);
    if (this.speed > this.peak) this.peak = this.speed;

    // Hand back to normal flight once slow enough near an envelope (or the edge), or when an exit was requested.
    const nearEnvelope = fd.distance - CRUISE.safetyMargin < (CRUISE.exitSpeed * CRUISE.exitSpeed) / (2 * this.accel) + CRUISE.exitSpeed * 2;
    let exit: CruiseExitReason | null = null;
    if (this.speed <= CRUISE.exitSpeed + 1e-6) {
      if (this.exiting) exit = this.exiting;
      else if (nearEnvelope) exit = 'approach';
    }

    // Integrate the system position with an exact segment/sphere sweep.
    _p1.copy(this.pos).addScaledVector(_fwd, this.speed * dt);
    for (const id of this.ids ?? BODY_IDS) {
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
    // Nor the system edge (the origin is fixed at zero).
    const te = segmentSphereExit(this.pos, _p1, _o, SYSTEM_EXTENT);
    if (te >= 0) {
      _p1.lerpVectors(this.pos, _p1, Math.max(0, te - 1e-6));
      this.speed = Math.min(this.speed, CRUISE.exitSpeed);
      this.safetyStops++;
      exit = 'safety';
    }
    this.pos.copy(_p1);
    if (exit) this.exiting = null;
    return { exit };
  }
}
