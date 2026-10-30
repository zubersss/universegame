import { Vector3 } from 'three';
import { KEEP_OUT } from './config';
import { surfaceReady } from './playSystem';
import { BODIES, BODY_IDS, type BodyDef, type BodyId } from '../world/bodies';

// Keep-out walls: no flying into a body that has no surface in play. Every
// body in play that is not surfaceReady (in M2 the Sun, Mercury, Venus and the
// giants) gets a soft spherical wall at keepOutRadius; every Quiet System body
// is surface-ready, so the Quiet System has none. Pure (system position and
// velocity in, velocity out) and Node-tested; Game applies it to the ship after
// each physics step while piloting. Cruise never reaches a wall: its envelopes
// (CRUISE.envelopeMargin) sit outside them.

/** Radius (m) of a body's keep-out wall: R + atmosphereHeight + KEEP_OUT.margin. */
export function keepOutRadius(def: BodyDef): number {
  return def.radius + def.atmosphereHeight + KEEP_OUT.margin;
}

/** The bodies in play with a keep-out wall: every one that is not surfaceReady. */
export function keepOutBodies(ids: readonly BodyId[] = BODY_IDS): BodyId[] {
  return ids.filter((id) => !surfaceReady(BODIES[id]));
}

/**
 * Lowest radial velocity (m/s, + = outward) allowed `gap` m outside a wall:
 * outside it the inward speed is limited so the ship can stop at the wall at
 * KEEP_OUT.decel; inside it (gap < 0) the ship is pushed out, harder with depth.
 */
export function minRadialSpeed(gap: number): number {
  return gap >= 0 ? -Math.sqrt(2 * KEEP_OUT.decel * gap) : Math.min(KEEP_OUT.maxPush, -gap * KEEP_OUT.pushGain);
}

export interface KeepOutState {
  /** The walled body whose warning band holds the ship, or null. */
  body: BodyId | null;
  /** Distance (m) outside that body's wall (negative inside); Infinity without a body. */
  gap: number;
  /** Whether the velocity was changed. */
  clamped: boolean;
}

const _n = new Vector3();

/**
 * Apply every keep-out wall in play to a ship at system position `pos` with
 * velocity `vel` (changed in place): the radial component is raised to
 * minRadialSpeed, the tangential one is left alone, so the ship can always fly
 * along or away from a wall. Returns (in `out`) the nearest wall within the
 * warning band.
 */
export function applyKeepOut(
  pos: Vector3, vel: Vector3, ids: readonly BodyId[] = BODY_IDS,
  out: KeepOutState = { body: null, gap: Infinity, clamped: false },
): KeepOutState {
  out.body = null;
  out.gap = Infinity;
  out.clamped = false;
  for (const id of ids) {
    const def = BODIES[id];
    if (surfaceReady(def)) continue;
    const c = def.center;
    _n.set(pos.x - c[0], pos.y - c[1], pos.z - c[2]);
    const d = _n.length();
    if (d < 1e-6) continue;
    _n.divideScalar(d);
    const gap = d - keepOutRadius(def);
    const vr = vel.dot(_n);
    const min = minRadialSpeed(gap);
    if (vr < min) {
      vel.addScaledVector(_n, min - vr);
      out.clamped = true;
    }
    if (gap < KEEP_OUT.warnBand && gap < out.gap) {
      out.body = id;
      out.gap = gap;
    }
  }
  return out;
}

/** The HUD warning near a wall, or null. */
export function keepOutWarning(s: KeepOutState): string | null {
  if (!s.body) return null;
  const def = BODIES[s.body];
  const why = def.kind === 'star' ? 'keep clear' : def.explore === 'zone' ? 'no solid ground; zone access not in this build' : 'no landing site in this build';
  return `Approach limit · ${def.name}: ${why}`;
}
