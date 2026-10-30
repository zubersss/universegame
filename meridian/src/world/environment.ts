import { Vector3 } from 'three';
import { BODIES, BODY_IDS, type BodyDef, type BodyId } from './bodies';

const _d = new Vector3();

function smooth(e0: number, e1: number, x: number): number {
  const t = Math.min(Math.max((x - e0) / (e1 - e0), 0), 1);
  return t * t * (3 - 2 * t);
}

/**
 * Radial gravity of one body at a system-relative offset d = p - C:
 * g = -d/|d| * gSurf * (R / max(|d|, R))^2, tapered smoothly to zero
 * between 2R and 4R (bounded gameplay approximation, not N-body).
 */
export function bodyGravity(def: BodyDef, dx: number, dy: number, dz: number, out: Vector3): Vector3 {
  const r = Math.hypot(dx, dy, dz);
  if (r < 1e-3) return out.set(0, 0, 0);
  const R = def.radius;
  const rr = Math.max(r, R);
  let g = def.gravity * (R / rr) * (R / rr);
  g *= 1 - smooth(2 * R, 4 * R, r);
  return out.set((-dx / r) * g, (-dy / r) * g, (-dz / r) * g);
}

/** Total gravity at a system position (only one body is ever within 4R). */
export function gravityAtSystem(p: Vector3, out: Vector3): Vector3 {
  out.set(0, 0, 0);
  for (const id of BODY_IDS) {
    const b = BODIES[id];
    bodyGravity(b, p.x - b.center[0], p.y - b.center[1], p.z - b.center[2], _d);
    out.add(_d);
  }
  return out;
}

/** Normalized air density (1 at the surface datum, 0 above the atmosphere / on airless bodies). */
export function airDensity(def: BodyDef, altitude: number): number {
  const a = def.atmosphere;
  if (!a) return 0;
  const x = altitude / def.atmosphereHeight;
  const fade = 1 - smooth(0.82, 1.0, x);
  return Math.exp(-Math.max(altitude, 0) / a.rayleighH) * fade;
}

/** The body whose center is nearest relative to its radius (the dominant body). */
export function dominantBody(p: Vector3): { id: BodyId; distance: number; radii: number } {
  let best: BodyId = BODY_IDS[0];
  let bestRadii = Infinity;
  let bestDist = 0;
  for (const id of BODY_IDS) {
    const b = BODIES[id];
    const d = Math.hypot(p.x - b.center[0], p.y - b.center[1], p.z - b.center[2]);
    const radii = d / b.radius;
    if (radii < bestRadii) {
      bestRadii = radii;
      best = id;
      bestDist = d;
    }
  }
  return { id: best, distance: bestDist, radii: bestRadii };
}
