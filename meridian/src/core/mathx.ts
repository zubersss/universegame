import { Matrix4, Quaternion, Vector3 } from 'three';

export const clamp = (x: number, a: number, b: number): number => (x < a ? a : x > b ? b : x);
export const saturate = (x: number): number => (x < 0 ? 0 : x > 1 ? 1 : x);
export const lerp = (a: number, b: number, t: number): number => a + (b - a) * t;
export const smoothstep = (e0: number, e1: number, x: number): number => {
  const t = saturate((x - e0) / (e1 - e0));
  return t * t * (3 - 2 * t);
};
/** Frame-rate independent exponential smoothing factor. */
export const expAlpha = (dt: number, tau: number): number => 1 - Math.exp(-dt / Math.max(tau, 1e-6));
export const DEG = Math.PI / 180;

/** Clamp vector magnitude in place. */
export function limitLength(v: Vector3, max: number): Vector3 {
  const l2 = v.lengthSq();
  if (l2 > max * max) v.multiplyScalar(max / Math.sqrt(l2));
  return v;
}

export function isFiniteVec(v: { x: number; y: number; z: number }): boolean {
  return Number.isFinite(v.x) && Number.isFinite(v.y) && Number.isFinite(v.z);
}

/**
 * Build an orthonormal tangent frame (right, forward) for a given up vector,
 * transporting a previous forward hint to avoid singularities near poles.
 */
export function tangentFrame(up: Vector3, forwardHint: Vector3, outForward: Vector3, outRight: Vector3): void {
  outForward.copy(forwardHint).addScaledVector(up, -forwardHint.dot(up));
  if (outForward.lengthSq() < 1e-10) {
    // Hint parallel to up: pick any perpendicular axis deterministically.
    outForward.set(1, 0, 0);
    if (Math.abs(up.x) > 0.9) outForward.set(0, 0, 1);
    outForward.addScaledVector(up, -outForward.dot(up));
  }
  outForward.normalize();
  outRight.crossVectors(outForward, up).normalize();
}

/** Quaternion that rotates the +Y axis onto `up` with minimal twist from `current`. */
export function alignUp(current: Quaternion, up: Vector3, out: Quaternion): Quaternion {
  const curUp = _v1.set(0, 1, 0).applyQuaternion(current);
  _q1.setFromUnitVectors(curUp, up);
  // premultiply is alias-safe (out may be `current`).
  return out.copy(current).premultiply(_q1).normalize();
}

/** Ray/sphere intersection. Returns [tNear, tFar] or null. dir must be normalized. */
export function raySphere(
  ox: number, oy: number, oz: number,
  dx: number, dy: number, dz: number,
  cx: number, cy: number, cz: number, r: number,
): [number, number] | null {
  const lx = ox - cx, ly = oy - cy, lz = oz - cz;
  const b = lx * dx + ly * dy + lz * dz;
  const c = lx * lx + ly * ly + lz * lz - r * r;
  const disc = b * b - c;
  if (disc < 0) return null;
  const s = Math.sqrt(disc);
  return [-b - s, -b + s];
}

/**
 * Exact segment/sphere test. Returns the fraction t in [0,1] at which the
 * segment p0->p1 first enters the sphere, 0 if p0 is already inside, or -1.
 */
export function segmentSphereEnter(p0: Vector3, p1: Vector3, c: Vector3, r: number): number {
  const dx = p1.x - p0.x, dy = p1.y - p0.y, dz = p1.z - p0.z;
  const fx = p0.x - c.x, fy = p0.y - c.y, fz = p0.z - c.z;
  const cc = fx * fx + fy * fy + fz * fz - r * r;
  if (cc <= 0) return 0;
  const a = dx * dx + dy * dy + dz * dz;
  if (a < 1e-12) return -1;
  const b = fx * dx + fy * dy + fz * dz;
  if (b >= 0) return -1; // moving away
  const disc = b * b - a * cc;
  if (disc < 0) return -1;
  const t = (-b - Math.sqrt(disc)) / a;
  return t >= 0 && t <= 1 ? t : -1;
}

/** Quaternion for a frame whose forward (-Z) is `fwd` and up (+Y) is close to `up`. */
export function quatFromForwardUp(fwd: Vector3, up: Vector3, out = new Quaternion()): Quaternion {
  const z = _z.copy(fwd).negate().normalize();
  const x = _x.crossVectors(up, z).normalize();
  const y = _y.crossVectors(z, x).normalize();
  _m.makeBasis(x, y, z);
  return out.setFromRotationMatrix(_m);
}

const _v1 = new Vector3();
const _q1 = new Quaternion();
const _x = new Vector3();
const _y = new Vector3();
const _z = new Vector3();
const _m = new Matrix4();
