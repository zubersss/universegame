import type { Vector3 } from 'three';

/**
 * Closest approach between a ray o + t*d (|d| = 1, 0 <= t <= maxT) and the
 * segment a..b. Returns the ray parameter and the distance at the closest
 * points, or null when the closest point lies behind the ray origin.
 */
export function rayCapsule(o: Vector3, d: Vector3, maxT: number, a: Vector3, b: Vector3): { t: number; dist: number } | null {
  const ux = b.x - a.x, uy = b.y - a.y, uz = b.z - a.z;
  const wx = o.x - a.x, wy = o.y - a.y, wz = o.z - a.z;
  const A = d.x * d.x + d.y * d.y + d.z * d.z; // 1
  const B = d.x * ux + d.y * uy + d.z * uz;
  const C = ux * ux + uy * uy + uz * uz;
  const D = d.x * wx + d.y * wy + d.z * wz;
  const E = ux * wx + uy * wy + uz * wz;
  const den = A * C - B * B;
  let s: number;
  let t: number;
  if (C < 1e-12) {
    // Degenerate segment: a point.
    s = 0;
    t = -D / A;
  } else if (den < 1e-12) {
    // Parallel: pick the segment start.
    s = 0;
    t = -D / A;
  } else {
    t = (B * E - C * D) / den;
    s = (A * E - B * D) / den;
  }
  // Clamp the segment parameter, then re-solve the ray parameter.
  if (s < 0 || s > 1) {
    s = Math.min(1, Math.max(0, s));
    t = (B * s - D) / A;
  }
  if (t < 0) return null;
  t = Math.min(t, maxT);
  // Re-solve s for the clamped t.
  if (C > 1e-12) s = Math.min(1, Math.max(0, (B * t + E) / C));
  const px = o.x + d.x * t - (a.x + ux * s);
  const py = o.y + d.y * t - (a.y + uy * s);
  const pz = o.z + d.z * t - (a.z + uz * s);
  return { t, dist: Math.sqrt(px * px + py * py + pz * pz) };
}

/** Scanner hold state for one target. */
export interface ScanTrack {
  id: string;
  progress: number;
  done: boolean;
  /** Seconds the tracked target has been out of the scan cone. */
  lost: number;
}

/**
 * idle: nothing tracked · scanning: progress advanced · paused: target briefly
 * lost, progress kept · complete: finished this step (exactly once per hold) ·
 * done: already finished, still aimed while F is held.
 */
export type ScanPhase = 'idle' | 'scanning' | 'paused' | 'complete' | 'done';

/** How long a target may leave the scan cone before its progress resets (s). */
export const SCAN_GRACE = 1.5;

export function newScanTrack(): ScanTrack {
  return { id: '', progress: 0, done: false, lost: 0 };
}

/**
 * Advance the scanner by dt while F is `holding`, aimed at `targetId` (null =
 * nothing in the cone). A moving target that slips out of the cone (or behind
 * another object) pauses progress for up to `grace` seconds instead of
 * resetting it; aiming back at it resumes. Releasing F resets everything.
 */
export function stepScanTrack(st: ScanTrack, holding: boolean, targetId: string | null, dt: number, holdTime: number, grace = SCAN_GRACE): ScanPhase {
  if (!holding) {
    st.id = '';
    st.progress = 0;
    st.done = false;
    st.lost = 0;
    return 'idle';
  }
  if (targetId !== null && targetId === st.id) {
    st.lost = 0;
    if (st.done) return 'done';
    st.progress += dt;
    if (st.progress < holdTime) return 'scanning';
    st.done = true;
    return 'complete';
  }
  // The tracked target is not in the cone this step.
  if (st.id !== '' && st.progress > 0 && !st.done && st.lost + dt <= grace) {
    st.lost += dt;
    return 'paused';
  }
  st.lost = 0;
  if (targetId === null) {
    st.progress = 0;
    return 'idle';
  }
  st.id = targetId;
  st.done = false;
  st.progress = dt;
  if (st.progress < holdTime) return 'scanning';
  st.done = true;
  return 'complete';
}
