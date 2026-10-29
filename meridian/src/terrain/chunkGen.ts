// Pure terrain chunk generation (runs in the worker; also used by tests).
// Grid: 33x33 vertices from shared finest-grid integer coordinates, plus a
// 2-sample apron for normals/parent normals, plus 4x33 skirt vertices.

import type { BodyDef, BodyId } from '../world/bodies';
import { CHUNK_GRID, CHUNK_VERTS, gridDir, gridResolution } from '../world/cube';
import type { SurfaceGenerator, SurfaceInfo } from '../world/surface';
import { tangentBasis, type V3 } from '../world/sites';

export const GRID_VERTS = CHUNK_VERTS * CHUNK_VERTS; // 1089
export const SKIRT_VERTS = 4 * CHUNK_VERTS; // 132
export const VERT_COUNT = GRID_VERTS + SKIRT_VERTS; // 1221
export const GRID_INDEX_COUNT = CHUNK_GRID * CHUNK_GRID * 6; // 6144
/** Tiling period (m) for planet-coordinate material lookups; all texture scales divide it. */
export const TILE_PERIOD = 1024;

const A = 2; // apron
const S = CHUNK_VERTS + 2 * A; // 37

export interface ChunkData {
  key: string;
  bodyId: BodyId;
  face: number;
  level: number;
  x: number;
  y: number;
  token: number;
  /** Planet-relative chunk origin (double precision). */
  center: [number, number, number];
  positions: Float32Array;
  normals: Float32Array;
  morphDelta: Float32Array;
  morphNormal: Int8Array;
  tile: Float32Array;
  attrs: Uint8Array;
  /** Bounding sphere (center relative to `center`, radius). */
  bounds: [number, number, number, number];
  minH: number;
  maxH: number;
  /** Max deviation of this chunk from its parent's surface (m). */
  ownError: number;
  skirt: number;
  genMs: number;
}

/** Shared index buffer: grid triangles first (collision uses only these), then skirts. */
export function makeChunkIndex(): Uint16Array {
  const idx: number[] = [];
  const V = CHUNK_VERTS;
  const g = (i: number, j: number) => j * V + i;
  for (let j = 0; j < CHUNK_GRID; j++) {
    for (let i = 0; i < CHUNK_GRID; i++) {
      // Fixed diagonal (i,j)-(i+1,j+1): matches the morph-target construction.
      idx.push(g(i, j), g(i + 1, j), g(i + 1, j + 1), g(i, j), g(i + 1, j + 1), g(i, j + 1));
    }
  }
  const sk = (e: number, k: number) => GRID_VERTS + e * V + k;
  for (let k = 0; k < CHUNK_GRID; k++) {
    // edge 0: j = 0 (outward -V); viewer's right = +U
    idx.push(g(k, 0), sk(0, k), sk(0, k + 1), g(k, 0), sk(0, k + 1), g(k + 1, 0));
    // edge 1: j = 32 (outward +V); viewer's right = -U
    idx.push(g(k + 1, V - 1), sk(1, k + 1), sk(1, k), g(k + 1, V - 1), sk(1, k), g(k, V - 1));
    // edge 2: i = 0 (outward -U); viewer's right = -V
    idx.push(g(0, k + 1), sk(2, k + 1), sk(2, k), g(0, k + 1), sk(2, k), g(0, k));
    // edge 3: i = 32 (outward +U); viewer's right = +V
    idx.push(g(V - 1, k), sk(3, k), sk(3, k + 1), g(V - 1, k), sk(3, k + 1), g(V - 1, k + 1));
  }
  return new Uint16Array(idx);
}

/** Grid spacing scale for a level (used for border normal finite differences). */
export function levelSpacing(def: BodyDef, level: number): number {
  return ((Math.PI / 2) * def.radius) / (CHUNK_GRID * 2 ** level);
}

const info: SurfaceInfo = { height: 0, biome: 0, variation: 0, special: 0, rockiness: 0 };

/** Normal from the continuous surface around `dir` using a canonical tangent frame. */
function surfaceNormal(gen: SurfaceGenerator, dir: V3, eps: number, out: number[]): void {
  const R = gen.R;
  const [t1, t2] = tangentBasis(dir);
  const k = eps / R;
  const p = (s1: number, s2: number): number[] => {
    let x = dir[0] + k * (s1 * t1[0] + s2 * t2[0]);
    let y = dir[1] + k * (s1 * t1[1] + s2 * t2[1]);
    let z = dir[2] + k * (s1 * t1[2] + s2 * t2[2]);
    const l = Math.sqrt(x * x + y * y + z * z);
    x /= l;
    y /= l;
    z /= l;
    const r = R + gen.height(x, y, z);
    return [x * r, y * r, z * r];
  };
  const a = p(1, 0);
  const b = p(-1, 0);
  const c = p(0, 1);
  const d = p(0, -1);
  const ux = a[0] - b[0], uy = a[1] - b[1], uz = a[2] - b[2];
  const vx = c[0] - d[0], vy = c[1] - d[1], vz = c[2] - d[2];
  let nx = uy * vz - uz * vy;
  let ny = uz * vx - ux * vz;
  let nz = ux * vy - uy * vx;
  const l = Math.sqrt(nx * nx + ny * ny + nz * nz) || 1;
  nx /= l;
  ny /= l;
  nz /= l;
  out[0] = nx;
  out[1] = ny;
  out[2] = nz;
}

const sstep = (e0: number, e1: number, x: number) => {
  const t = Math.min(1, Math.max(0, (x - e0) / (e1 - e0)));
  return t * t * (3 - 2 * t);
};

export function generateChunk(
  def: BodyDef,
  gen: SurfaceGenerator,
  face: number,
  level: number,
  x: number,
  y: number,
  token: number,
): ChunkData {
  const t0 = typeof performance !== 'undefined' ? performance.now() : 0;
  const R = def.radius;
  const M = gridResolution(def.maxLevel);
  const step = 2 ** (def.maxLevel - level);
  const gi0 = x * CHUNK_GRID * step;
  const gj0 = y * CHUNK_GRID * step;
  const V = CHUNK_VERTS;

  // Sample the apron grid (planet-relative double positions + directions).
  const P = new Float64Array(S * S * 3);
  const D = new Float64Array(S * S * 3);
  const biome = new Float32Array(GRID_VERTS);
  const variation = new Float32Array(GRID_VERTS);
  const special = new Float32Array(GRID_VERTS);
  const rocky = new Float32Array(GRID_VERTS);
  const dir = [0, 0, 0];
  let minH = Infinity;
  let maxH = -Infinity;
  for (let j = -A; j < V + A; j++) {
    for (let i = -A; i < V + A; i++) {
      gridDir(face, gi0 + i * step, gj0 + j * step, M, dir);
      gen.info(dir[0], dir[1], dir[2], info);
      const r = R + info.height;
      const o = ((j + A) * S + (i + A)) * 3;
      P[o] = dir[0] * r;
      P[o + 1] = dir[1] * r;
      P[o + 2] = dir[2] * r;
      D[o] = dir[0];
      D[o + 1] = dir[1];
      D[o + 2] = dir[2];
      if (i >= 0 && i < V && j >= 0 && j < V) {
        const g = j * V + i;
        biome[g] = info.biome;
        variation[g] = info.variation;
        special[g] = info.special;
        rocky[g] = info.rockiness;
        if (info.height < minH) minH = info.height;
        if (info.height > maxH) maxH = info.height;
      }
    }
  }
  const pi = (i: number, j: number) => ((j + A) * S + (i + A)) * 3;

  // Chunk origin: the surface point at the chunk center.
  const co = pi(16, 16);
  const cx = P[co];
  const cy = P[co + 1];
  const cz = P[co + 2];

  const positions = new Float32Array(VERT_COUNT * 3);
  const normals = new Float32Array(VERT_COUNT * 3);
  const morphDelta = new Float32Array(VERT_COUNT * 3);
  const morphNormal = new Int8Array(VERT_COUNT * 4);
  const tile = new Float32Array(VERT_COUNT * 3);
  const attrs = new Uint8Array(VERT_COUNT * 4);

  // Normals: central differences inside, continuous-surface normals on borders.
  const eps = levelSpacing(def, level);
  const nrm = [0, 0, 0];
  const nAt = new Float64Array(GRID_VERTS * 3);
  for (let j = 0; j < V; j++) {
    for (let i = 0; i < V; i++) {
      const g = j * V + i;
      if (i === 0 || j === 0 || i === V - 1 || j === V - 1) {
        const d = pi(i, j);
        surfaceNormal(gen, [D[d], D[d + 1], D[d + 2]], eps, nrm);
      } else {
        const a = pi(i + 1, j), b = pi(i - 1, j), c = pi(i, j + 1), d = pi(i, j - 1);
        const ux = P[a] - P[b], uy = P[a + 1] - P[b + 1], uz = P[a + 2] - P[b + 2];
        const vx = P[c] - P[d], vy = P[c + 1] - P[d + 1], vz = P[c + 2] - P[d + 2];
        nrm[0] = uy * vz - uz * vy;
        nrm[1] = uz * vx - ux * vz;
        nrm[2] = ux * vy - uy * vx;
        const l = Math.sqrt(nrm[0] * nrm[0] + nrm[1] * nrm[1] + nrm[2] * nrm[2]) || 1;
        nrm[0] /= l;
        nrm[1] /= l;
        nrm[2] /= l;
      }
      nAt[g * 3] = nrm[0];
      nAt[g * 3 + 1] = nrm[1];
      nAt[g * 3 + 2] = nrm[2];
    }
  }

  // Parent-level normals at even vertices (spacing 2 in this grid).
  const parentN = new Float64Array(GRID_VERTS * 3);
  if (level > 0) {
    for (let j = 0; j < V; j += 2) {
      for (let i = 0; i < V; i += 2) {
        const g = j * V + i;
        if (i === 0 || j === 0 || i === V - 1 || j === V - 1) {
          const d = pi(i, j);
          surfaceNormal(gen, [D[d], D[d + 1], D[d + 2]], eps * 2, nrm);
        } else {
          const a = pi(i + 2, j), b = pi(i - 2, j), c = pi(i, j + 2), d = pi(i, j - 2);
          const ux = P[a] - P[b], uy = P[a + 1] - P[b + 1], uz = P[a + 2] - P[b + 2];
          const vx = P[c] - P[d], vy = P[c + 1] - P[d + 1], vz = P[c + 2] - P[d + 2];
          nrm[0] = uy * vz - uz * vy;
          nrm[1] = uz * vx - ux * vz;
          nrm[2] = ux * vy - uy * vx;
          const l = Math.sqrt(nrm[0] * nrm[0] + nrm[1] * nrm[1] + nrm[2] * nrm[2]) || 1;
          nrm[0] /= l;
          nrm[1] /= l;
          nrm[2] /= l;
        }
        parentN[g * 3] = nrm[0];
        parentN[g * 3 + 1] = nrm[1];
        parentN[g * 3 + 2] = nrm[2];
      }
    }
  }

  // Grid vertices, morph targets and material attributes.
  let ownError = 0;
  let edgeError = 0;
  const tileOx = Math.floor(cx / TILE_PERIOD) * TILE_PERIOD;
  const tileOy = Math.floor(cy / TILE_PERIOD) * TILE_PERIOD;
  const tileOz = Math.floor(cz / TILE_PERIOD) * TILE_PERIOD;
  const pn = [0, 0, 0];
  for (let j = 0; j < V; j++) {
    for (let i = 0; i < V; i++) {
      const g = j * V + i;
      const p = pi(i, j);
      positions[g * 3] = P[p] - cx;
      positions[g * 3 + 1] = P[p + 1] - cy;
      positions[g * 3 + 2] = P[p + 2] - cz;
      normals[g * 3] = nAt[g * 3];
      normals[g * 3 + 1] = nAt[g * 3 + 1];
      normals[g * 3 + 2] = nAt[g * 3 + 2];
      tile[g * 3] = P[p] - tileOx;
      tile[g * 3 + 1] = P[p + 1] - tileOy;
      tile[g * 3 + 2] = P[p + 2] - tileOz;
      // Morph target on the parent's triangle surface.
      let tx = P[p], ty = P[p + 1], tz = P[p + 2];
      if (level > 0) {
        const oi = i & 1;
        const oj = j & 1;
        let a = -1, b = -1;
        if (oi && !oj) { a = pi(i - 1, j); b = pi(i + 1, j); }
        else if (!oi && oj) { a = pi(i, j - 1); b = pi(i, j + 1); }
        else if (oi && oj) { a = pi(i - 1, j - 1); b = pi(i + 1, j + 1); }
        if (a >= 0) {
          tx = (P[a] + P[b]) * 0.5;
          ty = (P[a + 1] + P[b + 1]) * 0.5;
          tz = (P[a + 2] + P[b + 2]) * 0.5;
          // Parent normal interpolated the same way.
          const ga = (oi && !oj) ? [g - 1, g + 1] : (!oi && oj) ? [g - V, g + V] : [g - V - 1, g + V + 1];
          pn[0] = parentN[ga[0] * 3] + parentN[ga[1] * 3];
          pn[1] = parentN[ga[0] * 3 + 1] + parentN[ga[1] * 3 + 1];
          pn[2] = parentN[ga[0] * 3 + 2] + parentN[ga[1] * 3 + 2];
        } else {
          pn[0] = parentN[g * 3];
          pn[1] = parentN[g * 3 + 1];
          pn[2] = parentN[g * 3 + 2];
        }
        const l = Math.sqrt(pn[0] * pn[0] + pn[1] * pn[1] + pn[2] * pn[2]) || 1;
        morphNormal[g * 4] = Math.round((pn[0] / l) * 127);
        morphNormal[g * 4 + 1] = Math.round((pn[1] / l) * 127);
        morphNormal[g * 4 + 2] = Math.round((pn[2] / l) * 127);
      } else {
        morphNormal[g * 4] = Math.round(normals[g * 3] * 127);
        morphNormal[g * 4 + 1] = Math.round(normals[g * 3 + 1] * 127);
        morphNormal[g * 4 + 2] = Math.round(normals[g * 3 + 2] * 127);
      }
      // Concavity for the terrain material (+ = hollow): height Laplacian over the grid spacing.
      // The apron guarantees the four neighbours exist; |lap| of a quarter spacing saturates.
      const pl = pi(i - 1, j), pr = pi(i + 1, j), pd = pi(i, j - 1), pu = pi(i, j + 1);
      const lap =
        Math.sqrt(P[pl] * P[pl] + P[pl + 1] * P[pl + 1] + P[pl + 2] * P[pl + 2]) +
        Math.sqrt(P[pr] * P[pr] + P[pr + 1] * P[pr + 1] + P[pr + 2] * P[pr + 2]) +
        Math.sqrt(P[pd] * P[pd] + P[pd + 1] * P[pd + 1] + P[pd + 2] * P[pd + 2]) +
        Math.sqrt(P[pu] * P[pu] + P[pu + 1] * P[pu + 1] + P[pu + 2] * P[pu + 2]) -
        4 * Math.sqrt(P[p] * P[p] + P[p + 1] * P[p + 1] + P[p + 2] * P[p + 2]);
      morphNormal[g * 4 + 3] = Math.max(-127, Math.min(127, Math.round((lap / eps) * 508)));
      const mdx = tx - P[p], mdy = ty - P[p + 1], mdz = tz - P[p + 2];
      morphDelta[g * 3] = mdx;
      morphDelta[g * 3 + 1] = mdy;
      morphDelta[g * 3 + 2] = mdz;
      const md = Math.sqrt(mdx * mdx + mdy * mdy + mdz * mdz);
      if (md > ownError) ownError = md;
      if ((i === 0 || j === 0 || i === V - 1 || j === V - 1) && md > edgeError) edgeError = md;
      // Material weights: biome, exposed rock (slope or ridge), variation, special.
      const d = p;
      const up = normals[g * 3] * D[d] + normals[g * 3 + 1] * D[d + 1] + normals[g * 3 + 2] * D[d + 2];
      const slope = 1 - up;
      const rock = Math.max(rocky[g], sstep(0.09, 0.3, slope));
      attrs[g * 4] = Math.round(biome[g] * 255);
      attrs[g * 4 + 1] = Math.round(Math.min(1, rock) * 255);
      attrs[g * 4 + 2] = Math.round(variation[g] * 255);
      attrs[g * 4 + 3] = Math.round(special[g] * 255);
    }
  }

  // Skirts hang radially below each border vertex, sized to cover a one-level
  // neighbor's error (the edge morph deltas) with margin.
  const skirt = level === 0 ? 250 : Math.max(2, 2 * edgeError + 1 + eps * 0.02);
  const borderIndex = (e: number, k: number): [number, number] =>
    e === 0 ? [k, 0] : e === 1 ? [k, V - 1] : e === 2 ? [0, k] : [V - 1, k];
  for (let e = 0; e < 4; e++) {
    for (let k = 0; k < V; k++) {
      const [i, j] = borderIndex(e, k);
      const g = j * V + i;
      const s = GRID_VERTS + e * V + k;
      const d = pi(i, j);
      positions[s * 3] = positions[g * 3] - D[d] * skirt;
      positions[s * 3 + 1] = positions[g * 3 + 1] - D[d + 1] * skirt;
      positions[s * 3 + 2] = positions[g * 3 + 2] - D[d + 2] * skirt;
      for (let c = 0; c < 3; c++) {
        normals[s * 3 + c] = normals[g * 3 + c];
        morphDelta[s * 3 + c] = morphDelta[g * 3 + c];
        tile[s * 3 + c] = tile[g * 3 + c] - D[d + c] * skirt;
      }
      for (let c = 0; c < 4; c++) {
        morphNormal[s * 4 + c] = morphNormal[g * 4 + c];
        attrs[s * 4 + c] = attrs[g * 4 + c];
      }
    }
  }

  // Bounding sphere around the vertex centroid (including skirts and morph extremes).
  let bx = 0, by = 0, bz = 0;
  for (let v = 0; v < VERT_COUNT; v++) {
    bx += positions[v * 3];
    by += positions[v * 3 + 1];
    bz += positions[v * 3 + 2];
  }
  bx /= VERT_COUNT;
  by /= VERT_COUNT;
  bz /= VERT_COUNT;
  let br = 0;
  for (let v = 0; v < VERT_COUNT; v++) {
    for (const k of [0, 1]) {
      const qx = positions[v * 3] + k * morphDelta[v * 3] - bx;
      const qy = positions[v * 3 + 1] + k * morphDelta[v * 3 + 1] - by;
      const qz = positions[v * 3 + 2] + k * morphDelta[v * 3 + 2] - bz;
      const r = qx * qx + qy * qy + qz * qz;
      if (r > br) br = r;
    }
  }

  return {
    key: `${face}/${level}/${x}/${y}`,
    bodyId: def.id,
    face,
    level,
    x,
    y,
    token,
    center: [cx, cy, cz],
    positions,
    normals,
    morphDelta,
    morphNormal,
    tile,
    attrs,
    bounds: [bx, by, bz, Math.sqrt(br)],
    minH,
    maxH,
    ownError,
    skirt,
    genMs: (typeof performance !== 'undefined' ? performance.now() : 0) - t0,
  };
}

/** Transferable buffers of a chunk (for postMessage). */
export function chunkTransfers(c: ChunkData): ArrayBuffer[] {
  return [c.positions, c.normals, c.morphDelta, c.morphNormal, c.tile, c.attrs].map((a) => a.buffer as ArrayBuffer);
}

/** Approximate byte size of a chunk's arrays. */
export function chunkBytes(c: ChunkData): number {
  return c.positions.byteLength + c.normals.byteLength + c.morphDelta.byteLength + c.morphNormal.byteLength + c.tile.byteLength + c.attrs.byteLength;
}
