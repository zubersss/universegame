import type { BodyDef } from '../world/bodies';
import type { SurfaceGenerator, SurfaceInfo } from '../world/surface';
import { chunkBounds, faceDir } from '../world/cube';
import { tangentBasis, LANDING_R0, RELAY_R1, type MissionSites, type V3 } from '../world/sites';
import { hashCombine } from '../core/rng';
import type { FaunaSpecies } from './faunaSpecies';

// Deterministic creature spawn points. Spawn cells are cube-sphere chunks
// three levels above the contact level (~740 m on Ilex). Each cell owns a
// few herd candidates per species, hashed from (body seed, 'fauna', species
// id, cell, candidate) — the species *id* rather than its index, so appending
// species never moves existing herds. Spawns depend only on the seed and the
// surface generator, never on time, order or the player.

export const SPAWN_LEVEL_OFFSET = 3;

export interface Spawn {
  /** Stable object ID (scan record): `${body}:fauna:${species}:${face}/${x}/${y}:${k}:${m}`. */
  id: string;
  species: FaunaSpecies;
  /** Home point direction (unit) and its tangent frame. */
  home: V3;
  t1: V3;
  t2: V3;
  /** Start offset from home in the tangent frame (m). */
  x: number;
  z: number;
  yaw: number;
  /** Instance height (m). */
  h: number;
  /** Per-creature runtime PRNG seed. */
  seed: number;
}

export function spawnLevel(def: BodyDef): number {
  return Math.max(0, def.maxLevel - SPAWN_LEVEL_OFFSET);
}

function hf(h: number, k: number): number {
  return hashCombine(h, k) / 4294967296;
}

const info: SurfaceInfo = { height: 0, biome: 0, variation: 0, special: 0, rockiness: 0 };
const d: number[] = [0, 0, 0];

/** Keep herds' homes out of the landing clearing and relay pad. */
function excluded(sites: MissionSites, R: number, dir: number[], margin: number): boolean {
  const l = sites.landing.dir;
  const r = sites.relay.dir;
  const dl = Math.hypot(dir[0] - l[0], dir[1] - l[1], dir[2] - l[2]) * R;
  const dr = Math.hypot(dir[0] - r[0], dir[1] - r[1], dir[2] - r[2]) * R;
  return dl < LANDING_R0 + margin || dr < RELAY_R1 + margin;
}

/** All creatures spawned in one spawn cell (`face/level/x/y` at spawnLevel). */
export function spawnCell(
  def: BodyDef, gen: SurfaceGenerator, sites: MissionSites, species: readonly FaunaSpecies[],
  face: number, x: number, y: number,
): Spawn[] {
  const level = spawnLevel(def);
  const b = chunkBounds(level, x, y);
  const R = def.radius;
  const eps = 1.5 / R;
  const out: Spawn[] = [];
  for (const sp of species) {
    for (let k = 0; k < sp.candidates; k++) {
      const h = hashCombine(def.seed, 'fauna', sp.id, face, x, y, k);
      faceDir(face, b.u0 + (b.u1 - b.u0) * hf(h, 1), b.v0 + (b.v1 - b.v0) * hf(h, 2), d);
      if (excluded(sites, R, d, sp.behaviour.homeRadius)) continue;
      gen.info(d[0], d[1], d[2], info);
      const home: V3 = [d[0], d[1], d[2]];
      const [t1, t2] = tangentBasis(home);
      const h0 = info.height;
      const ha = gen.height(d[0] + eps * t1[0], d[1] + eps * t1[1], d[2] + eps * t1[2]);
      const hb = gen.height(d[0] + eps * t2[0], d[1] + eps * t2[1], d[2] + eps * t2[2]);
      const gx = (ha - h0) / 1.5;
      const gy = (hb - h0) / 1.5;
      const slope = 1 - 1 / Math.sqrt(1 + gx * gx + gy * gy);
      if (slope > sp.maxSlope) continue;
      if (hf(h, 3) >= sp.habitat(info, slope)) continue;
      const n = sp.groupMin + Math.floor(hf(h, 4) * (sp.groupMax - sp.groupMin + 1));
      for (let m = 0; m < n; m++) {
        const hm = hashCombine(h, m);
        const r = sp.behaviour.homeRadius * 0.6 * Math.sqrt(hf(hm, 1));
        const a = hf(hm, 2) * Math.PI * 2;
        out.push({
          id: `${def.id}:fauna:${sp.id}:${face}/${x}/${y}:${k}:${m}`,
          species: sp,
          home, t1, t2,
          x: Math.sin(a) * r,
          z: Math.cos(a) * r,
          yaw: hf(hm, 3) * Math.PI * 2 - Math.PI,
          h: sp.hMin + (sp.hMax - sp.hMin) * hf(hm, 4),
          seed: hashCombine(hm, 'rt'),
        });
      }
    }
  }
  return out;
}

/**
 * Unit direction of a point at tangent offset (x, z) m from a home direction
 * on a sphere of radius R (exact on the sphere, no small-angle drift).
 */
export function offsetDir(home: V3, t1: V3, t2: V3, x: number, z: number, R: number, out: number[]): number[] {
  const px = home[0] + (x * t1[0] + z * t2[0]) / R;
  const py = home[1] + (x * t1[1] + z * t2[1]) / R;
  const pz = home[2] + (x * t1[2] + z * t2[2]) / R;
  const l = Math.sqrt(px * px + py * py + pz * pz);
  out[0] = px / l;
  out[1] = py / l;
  out[2] = pz / l;
  return out;
}
