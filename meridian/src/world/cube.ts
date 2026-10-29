// Cube-sphere parameterization shared by the terrain worker and main thread.
// Face f covers cube points N + u*U + v*V for pre-warp u, v in [-1, 1]. All
// vertex directions are derived from integer grid coordinates on the finest
// grid so shared edges and corners produce bit-identical directions.

export const CHUNK_GRID = 32; // quads per chunk side
export const CHUNK_VERTS = CHUNK_GRID + 1; // 33

type V3 = readonly [number, number, number];

export interface Face {
  n: V3;
  u: V3;
  v: V3;
}

// Right-handed: cross(U, V) = N for every face.
export const FACES: readonly Face[] = [
  { n: [1, 0, 0], u: [0, 0, -1], v: [0, 1, 0] }, // +X
  { n: [-1, 0, 0], u: [0, 0, 1], v: [0, 1, 0] }, // -X
  { n: [0, 1, 0], u: [1, 0, 0], v: [0, 0, -1] }, // +Y
  { n: [0, -1, 0], u: [1, 0, 0], v: [0, 0, 1] }, // -Y
  { n: [0, 0, 1], u: [1, 0, 0], v: [0, 1, 0] }, // +Z
  { n: [0, 0, -1], u: [-1, 0, 0], v: [0, 1, 0] }, // -Z
];

// Odd polynomial approximating tan(pi*t/4)/tan(pi/4) for more uniform cells.
// warp(t) = t * (1 - (1 - t^2) * (A + B t^2)); exactly +-1 at t = +-1 and
// exactly odd-symmetric (t is used only through t and t*t).
const WA = 0.2146;
const WB = 0.0531;

export function warp(t: number): number {
  const t2 = t * t;
  return t * (1 - (1 - t2) * (WA + WB * t2));
}

/** Inverse of warp (Newton iterations; only used for lookups, not geometry). */
export function unwarp(w: number): number {
  let t = w;
  for (let i = 0; i < 6; i++) {
    const t2 = t * t;
    const f = t * (1 - (1 - t2) * (WA + WB * t2)) - w;
    // d/dt of (1-A)t + (A-B)t^3 + B t^5
    const df = 1 - WA + 3 * (WA - WB) * t2 + 5 * WB * t2 * t2;
    t -= f / df;
  }
  return t;
}

/** Finest-grid resolution for a body: CHUNK_GRID * 2^maxLevel intervals per face edge. */
export function gridResolution(maxLevel: number): number {
  return CHUNK_GRID * 2 ** maxLevel;
}

/**
 * Direction for integer finest-grid coordinates (gi, gj) on `face` with
 * resolution M. gi/gj may lie slightly outside [0, M] (apron samples).
 */
export function gridDir(face: number, gi: number, gj: number, M: number, out: number[] | Float64Array): void {
  const u = warp(-1 + (2 * gi) / M);
  const v = warp(-1 + (2 * gj) / M);
  const f = FACES[face];
  const x = f.n[0] + u * f.u[0] + v * f.v[0];
  const y = f.n[1] + u * f.u[1] + v * f.v[1];
  const z = f.n[2] + u * f.u[2] + v * f.v[2];
  const l = Math.sqrt(x * x + y * y + z * z);
  out[0] = x / l;
  out[1] = y / l;
  out[2] = z / l;
}

/** Direction for continuous pre-warp face coordinates (u, v in [-1, 1]). */
export function faceDir(face: number, u: number, v: number, out: number[] | Float64Array): void {
  const wu = warp(u);
  const wv = warp(v);
  const f = FACES[face];
  const x = f.n[0] + wu * f.u[0] + wv * f.v[0];
  const y = f.n[1] + wu * f.u[1] + wv * f.v[1];
  const z = f.n[2] + wu * f.u[2] + wv * f.v[2];
  const l = Math.sqrt(x * x + y * y + z * z);
  out[0] = x / l;
  out[1] = y / l;
  out[2] = z / l;
}

/**
 * Map a direction (need not be normalized) to its face and pre-warp face
 * coordinates. Ties on cube edges resolve deterministically by axis order.
 */
export function dirToFace(x: number, y: number, z: number): { face: number; u: number; v: number } {
  const ax = Math.abs(x);
  const ay = Math.abs(y);
  const az = Math.abs(z);
  let face: number;
  if (ax >= ay && ax >= az) face = x >= 0 ? 0 : 1;
  else if (ay >= az) face = y >= 0 ? 2 : 3;
  else face = z >= 0 ? 4 : 5;
  const f = FACES[face];
  const d = x * f.n[0] + y * f.n[1] + z * f.n[2];
  const px = x / d;
  const py = y / d;
  const pz = z / d;
  const wu = px * f.u[0] + py * f.u[1] + pz * f.u[2];
  const wv = px * f.v[0] + py * f.v[1] + pz * f.v[2];
  return { face, u: unwarp(Math.max(-1, Math.min(1, wu))), v: unwarp(Math.max(-1, Math.min(1, wv))) };
}

/** Chunk key string. */
export function chunkKey(face: number, level: number, x: number, y: number): string {
  return `${face}/${level}/${x}/${y}`;
}

/** The chunk (at `level`) containing pre-warp face coordinates (u, v). */
export function chunkAt(face: number, u: number, v: number, level: number): { x: number; y: number } {
  const n = 2 ** level;
  const x = Math.min(n - 1, Math.max(0, Math.floor(((u + 1) / 2) * n)));
  const y = Math.min(n - 1, Math.max(0, Math.floor(((v + 1) / 2) * n)));
  return { x, y };
}

/** Pre-warp face-coordinate bounds of a chunk. */
export function chunkBounds(level: number, x: number, y: number): { u0: number; u1: number; v0: number; v1: number } {
  const s = 2 / 2 ** level;
  return { u0: -1 + x * s, u1: -1 + (x + 1) * s, v0: -1 + y * s, v1: -1 + (y + 1) * s };
}

/**
 * Cube point (not normalized) for pre-warp coordinates that may lie slightly
 * outside a face; used to step across face edges for neighbor lookups.
 */
export function faceCubePoint(face: number, u: number, v: number): [number, number, number] {
  const f = FACES[face];
  const wu = warp(u);
  const wv = warp(v);
  return [f.n[0] + wu * f.u[0] + wv * f.v[0], f.n[1] + wu * f.u[1] + wv * f.v[1], f.n[2] + wu * f.u[2] + wv * f.v[2]];
}
