import { Quaternion, Vector3 } from 'three';
import { GROUP, GROUPS, type Physics } from '../physics/Physics';
import { LANDING } from '../game/config';
import { GEAR_FEET } from './ShipModel';
import type { ShipSim } from './Ship';
import type { FlightOverride } from './FlightModel';

export interface FootprintProbe {
  hits: number;
  /** Distance from each pad bottom down to the ground along -up (NaN on miss). */
  gaps: [number, number, number];
  minGap: number;
  maxGap: number;
  /** Angle between the footprint plane and the local horizontal (deg). */
  slopeDeg: number;
  /** Footprint plane normal (oriented up). */
  normal: Vector3;
  obstructed: boolean;
  /** Why landing here is not allowed (null when suitable). */
  reason: string | null;
}

const _o = new Vector3();
const _p = [new Vector3(), new Vector3(), new Vector3()];
const _hn = [new Vector3(), new Vector3(), new Vector3()];
const _a = new Vector3();
const _b = new Vector3();
const _qi = new Quaternion();
const _shipUp = new Vector3();
const _w = new Vector3();

export function emptyProbe(): FootprintProbe {
  return { hits: 0, gaps: [NaN, NaN, NaN], minGap: NaN, maxGap: NaN, slopeDeg: 90, normal: new Vector3(), obstructed: false, reason: 'No ground detected' };
}

/** Raycast below each landing pad (actual gear footprint) against terrain and props. */
export function probeFootprint(physics: Physics, ship: ShipSim, up: Vector3, out: FootprintProbe): FootprintProbe {
  out.hits = 0;
  out.obstructed = false;
  let minG = Infinity;
  let maxG = -Infinity;
  for (let i = 0; i < 3; i++) {
    ship.localToWorld(GEAR_FEET[i], _o).addScaledVector(up, 2);
    const hit = physics.castRay(_o.x, _o.y, _o.z, -up.x, -up.y, -up.z, 300, GROUPS.queryStatic, ship.body);
    if (!hit) {
      out.gaps[i] = NaN;
      continue;
    }
    out.hits++;
    const g = hit.toi - 2;
    out.gaps[i] = g;
    minG = Math.min(minG, g);
    maxG = Math.max(maxG, g);
    _p[i].copy(_o).addScaledVector(up, -hit.toi);
    _hn[i].set(hit.nx, hit.ny, hit.nz);
    if ((hit.collider.collisionGroups() >>> 16) & GROUP.PROPS) out.obstructed = true;
  }
  out.minGap = out.hits ? minG : NaN;
  out.maxGap = out.hits ? maxG : NaN;
  if (out.hits < 3) {
    out.slopeDeg = 90;
    out.reason = out.hits === 0 ? 'No ground detected below the gear' : 'Uneven ground: a landing pad has no support';
    return out;
  }
  _a.copy(_p[1]).sub(_p[0]);
  _b.copy(_p[2]).sub(_p[0]);
  out.normal.crossVectors(_a, _b).normalize();
  if (out.normal.dot(up) < 0) out.normal.negate();
  out.slopeDeg = (Math.acos(Math.min(1, out.normal.dot(up))) * 180) / Math.PI;
  // Rocks/steps under a pad show up as normals far from the footprint plane.
  for (let i = 0; i < 3; i++) if (_hn[i].dot(out.normal) < Math.cos((28 * Math.PI) / 180)) out.obstructed = true;
  if (out.obstructed) out.reason = 'Landing zone obstructed';
  else if (out.slopeDeg > LANDING.maxSlopeDeg) out.reason = `Surface too steep (${out.slopeDeg.toFixed(0)}° > ${LANDING.maxSlopeDeg}°)`;
  else out.reason = null;
  return out;
}

export type AssistPhase = 'braking' | 'descending' | 'holding';

/**
 * Landing assist: brake, align gradually to the footprint plane, descend
 * slowly, and hold at a safe height with a reason when the site is unsuitable.
 */
export class LandingAssist {
  active = false;
  phase: AssistPhase = 'braking';
  reason: string | null = null;
  /** Seconds of stable supported contact (touchdown requires LANDING.stableTime). */
  stable = 0;

  engage(): void {
    this.active = true;
    this.phase = 'braking';
    this.stable = 0;
  }

  disengage(): void {
    this.active = false;
    this.reason = null;
    this.stable = 0;
  }

  /** Build the flight override for this step. */
  compute(ship: ShipSim, up: Vector3, probe: FootprintProbe, yawInput: number, out: FlightOverride): void {
    const v = ship.vel;
    const vVert = v.dot(up);
    const tangential = Math.sqrt(Math.max(0, v.lengthSq() - vVert * vVert));
    const gap = Number.isFinite(probe.minGap) ? probe.minGap : 30;
    this.reason = probe.reason;
    let vz: number;
    if (probe.reason === null && tangential <= LANDING.maxTangential) {
      this.phase = 'descending';
      vz = gap > 12 ? -LANDING.descentFar : gap > 3 ? -2.5 : -LANDING.descentNear;
    } else if (probe.reason === null) {
      this.phase = 'braking';
      vz = Math.max(-2, Math.min(2, (LANDING.holdAltitude + 3 - gap) * 0.6));
    } else {
      this.phase = 'holding';
      vz = Math.max(-3, Math.min(3, (LANDING.holdAltitude - gap) * 0.8));
    }
    out.vTarget.copy(up).multiplyScalar(vz);
    out.tau = 0.6;
    out.aMax = 20;
    // Align ship up toward the footprint plane (or radial up when unsuitable).
    ship.up(_shipUp);
    const target = probe.reason === null && probe.hits === 3 ? probe.normal : up;
    _w.crossVectors(_shipUp, target);
    const s = _w.length();
    const angle = Math.atan2(s, _shipUp.dot(target));
    if (s > 1e-6) _w.multiplyScalar((Math.min(angle / 0.5, 0.8) / s));
    else _w.set(0, 0, 0);
    // Pilot may still yaw while assisted.
    _w.addScaledVector(_shipUp, -yawInput * 0.6);
    _qi.copy(ship.currQuat).invert();
    out.angTargetLocal.copy(_w).applyQuaternion(_qi);
  }

  /**
   * Touchdown check: all pads in contact, suitable surface, nearly at rest,
   * held for LANDING.stableTime. Returns true when the ship may be parked.
   */
  touchdown(dt: number, ship: ShipSim, up: Vector3, probe: FootprintProbe): boolean {
    const contact =
      probe.hits === 3 && probe.maxGap <= LANDING.contactTolerance && probe.reason === null;
    const vVert = ship.vel.dot(up);
    const resting = ship.vel.length() < 0.6 && Math.abs(vVert) < 0.5 && ship.angvel.length() < 0.15;
    if (contact && resting) this.stable += dt;
    else this.stable = 0;
    return this.stable >= LANDING.stableTime;
  }
}
