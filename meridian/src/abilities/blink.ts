import { Vector3 } from 'three';
import type { BlinkParams } from './types';

// The blink primitive (Lunar Step; Anchor Blink is a variant with anchor
// points). Charter K: hold right mouse to preview, Q or click to commit;
// range 60 m, cooldown 1.2 s, line of sight required, arrival velocity 0,
// target clearance by capsule test, ground within 2 m (or, when airborne,
// within 3 m) below the target. Charter J: a blink commits only after the
// range, line-of-sight, clearance and loaded-collision checks pass; it never
// commits into unloaded or solid space; a failed check gives red feedback and
// consumes nothing (no cooldown).

export interface BlinkSense {
  /** Radial up. */
  up: Vector3;
  /** Eye (aim origin) and aim direction (unit). */
  eye: Vector3;
  aim: Vector3;
  /** Whether the blinker stands on the ground. */
  grounded: boolean;
  /** First hit along a ray (distance and normal), or null within maxDist. */
  ray(origin: Vector3, dir: Vector3, maxDist: number): { dist: number; normal: Vector3 } | null;
  /** Ground below a point: distance down to it, or null within maxDist. */
  groundBelow(point: Vector3, maxDist: number): number | null;
  /** The walker's capsule fits with its feet at this point (nothing intersecting). */
  fits(feet: Vector3): boolean;
  /** Collision is loaded around this point. */
  ready(point: Vector3): boolean;
}

export type BlinkFailure = 'cooldown' | 'no target' | 'out of range' | 'no ground' | 'blocked' | 'no line of sight' | 'not loaded';

export interface BlinkTarget {
  ok: boolean;
  /** Feet point to arrive at (valid only when ok, otherwise the best guess for the marker). */
  feet: Vector3;
  /** Distance from the eye to the target point (m). */
  distance: number;
  /** Why it is refused (null when ok). */
  reason: BlinkFailure | null;
}

/** Feet sit this far above the ground found under the target (controller skin and a little). */
const ARRIVE_LIFT = 0.05;
/** The target is pulled back along the aim from a hit surface by this much (m). */
const SURFACE_BACKOFF = 0.45;

const _p = new Vector3();
const _d = new Vector3();

export class Blink {
  /** Seconds until the next blink is allowed. */
  cooldown = 0;
  /** Blinks committed (diagnostics). */
  count = 0;

  constructor(readonly p: BlinkParams) {}

  tick(dt: number): void {
    this.cooldown = Math.max(0, this.cooldown - dt);
  }

  /** Resolve the aim into a target, running every charter J check. */
  target(s: BlinkSense, out: BlinkTarget = { ok: false, feet: new Vector3(), distance: 0, reason: null }): BlinkTarget {
    const p = this.p;
    const range = p.range;
    out.ok = false;
    out.reason = null;
    // Aim: the first surface along the look within range, else the point at range.
    const hit = s.ray(s.eye, s.aim, range);
    const dist = hit ? Math.max(0, hit.dist - SURFACE_BACKOFF) : range;
    _p.copy(s.eye).addScaledVector(s.aim, dist);
    // Ground below the aim point: standing targets need it within groundWithin;
    // airborne blinkers may arrive up to airborneWithin above it.
    const allowed = s.grounded ? p.groundWithin : p.airborneWithin;
    const below = s.groundBelow(_p, allowed + 1.0);
    out.feet.copy(_p);
    out.distance = dist;
    if (below === null || below > allowed) {
      out.reason = hit ? 'no ground' : 'no target';
      return out;
    }
    // Stand on the ground when it is within reach of standing, else hover where aimed.
    if (below <= p.groundWithin) out.feet.addScaledVector(s.up, -below + ARRIVE_LIFT);
    out.distance = _d.copy(out.feet).sub(s.eye).length();
    if (out.distance > range + 0.5) {
      out.reason = 'out of range';
      return out;
    }
    if (!s.ready(out.feet)) {
      out.reason = 'not loaded';
      return out;
    }
    // Line of sight from the eye to the target's chest height.
    _p.copy(out.feet).addScaledVector(s.up, 1.2);
    _d.copy(_p).sub(s.eye);
    const len = _d.length();
    if (len > 1e-6) {
      const los = s.ray(s.eye, _d.divideScalar(len), len);
      if (los && los.dist < len - 0.3) {
        out.reason = 'no line of sight';
        return out;
      }
    }
    if (!s.fits(out.feet)) {
      out.reason = 'blocked';
      return out;
    }
    if (this.cooldown > 0) {
      out.reason = 'cooldown';
      return out;
    }
    out.ok = true;
    return out;
  }

  /** Commit a resolved target: starts the cooldown. Returns false (and consumes nothing) if it is not ok. */
  commit(t: BlinkTarget): boolean {
    if (!t.ok) return false;
    this.cooldown = this.p.cooldown;
    this.count++;
    return true;
  }
}
