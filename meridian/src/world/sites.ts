// Deterministic mission sites: one landing clearing, one relay pad and three
// sample positions per body. Selection is a bounded search over a fixed set of
// candidates using arithmetic only (no transcendental functions), so every
// context (main thread, worker, other browsers) picks the same site.

import { BODIES, sunDirFor, type BodyDef, type BodyId } from './bodies';
import { faceDir } from './cube';
import { SurfaceGenerator, type Clearing, type SurfaceInfo } from './surface';
import { hashCombine } from '../core/rng';

export type V3 = [number, number, number];

export interface SampleSite {
  id: string;
  dir: V3;
}

export interface MissionSites {
  bodyId: BodyId;
  landing: { dir: V3; height: number };
  relay: { id: string; dir: V3; height: number };
  samples: SampleSite[];
  clearings: Clearing[];
}

export const LANDING_R0 = 55;
export const LANDING_R1 = 150;
export const RELAY_R0 = 9;
export const RELAY_R1 = 30;
const RELAY_DISTANCE = 190;

// 8 bearings as exact-ish constant unit vectors (no trig at runtime).
const S2 = 0.7071067811865476;
const BEARINGS: [number, number][] = [[1, 0], [S2, S2], [0, 1], [-S2, S2], [-1, 0], [-S2, -S2], [0, -1], [S2, -S2]];
// 12 ring sample bearings (30 degree steps).
const C30 = 0.8660254037844386;
const RING: [number, number][] = [
  [1, 0], [C30, 0.5], [0.5, C30], [0, 1], [-0.5, C30], [-C30, 0.5],
  [-1, 0], [-C30, -0.5], [-0.5, -C30], [0, -1], [0.5, -C30], [C30, -0.5],
];

function norm(v: V3): V3 {
  const l = Math.sqrt(v[0] * v[0] + v[1] * v[1] + v[2] * v[2]);
  return [v[0] / l, v[1] / l, v[2] / l];
}
function dot(a: V3, b: readonly number[]): number {
  return a[0] * b[0] + a[1] * b[1] + a[2] * b[2];
}
function cross(a: V3, b: V3): V3 {
  return [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]];
}

/** Deterministic tangent frame at n. */
export function tangentBasis(n: V3): [V3, V3] {
  const ref: V3 = Math.abs(n[1]) < 0.9 ? [0, 1, 0] : [1, 0, 0];
  const t1 = norm(cross(ref, n));
  const t2 = cross(n, t1);
  return [t1, t2];
}

/** Move along the surface from n by `dist` meters in tangent direction (c, s) of the basis. */
export function offsetDir(n: V3, basis: [V3, V3], c: number, s: number, dist: number, R: number): V3 {
  const k = dist / R;
  const [t1, t2] = basis;
  return norm([
    n[0] + k * (c * t1[0] + s * t2[0]),
    n[1] + k * (c * t1[1] + s * t2[1]),
    n[2] + k * (c * t1[2] + s * t2[2]),
  ]);
}

interface Prefs {
  sunLo: number; // min dot(n, sun) (sin of min elevation)
  sunHi: number;
  face: V3 | null; // preferred facing direction (toward the expected approach)
  faceMin: number;
  biomeLo: number;
  biomeHi: number;
}

function dirTo(a: BodyDef, b: BodyDef): V3 {
  return norm([b.center[0] - a.center[0], b.center[1] - a.center[1], b.center[2] - a.center[2]]);
}

function prefsFor(def: BodyDef): Prefs {
  const B = BODIES;
  switch (def.id) {
    case 'ilex': // groves near chalk ridges; Vesper above the horizon
      return { sunLo: 0.31, sunHi: 0.53, face: dirTo(B.ilex, B.vesper), faceMin: 0.05, biomeLo: 0.55, biomeHi: 0.88 };
    case 'vesper': // dunes against mesa country; facing the approach from Ilex
      return { sunLo: 0.34, sunHi: 0.57, face: dirTo(B.vesper, B.ilex), faceMin: 0.15, biomeLo: 0.3, biomeHi: 0.72 };
    default: // rime basin near the terminator; facing the approach from Vesper
      return { sunLo: 0.17, sunHi: 0.41, face: dirTo(B.cairn, B.vesper), faceMin: -0.1, biomeLo: 0.55, biomeHi: 1.01 };
  }
}

const info: SurfaceInfo = { height: 0, biome: 0, variation: 0, special: 0, rockiness: 0 };

/** Mean and roughness of base heights over a ring of radius r around n. */
function flatness(gen: SurfaceGenerator, n: V3, r: number): { mean: number; rough: number } {
  const R = gen.R;
  const basis = tangentBasis(n);
  const hs: number[] = [gen.baseInfo(n[0], n[1], n[2], info).height];
  for (const [c, s] of RING) {
    const d = offsetDir(n, basis, c, s, r, R);
    hs.push(gen.baseInfo(d[0], d[1], d[2], info).height);
    const d2 = offsetDir(n, basis, c, s, r * 0.5, R);
    hs.push(gen.baseInfo(d2[0], d2[1], d2[2], info).height);
  }
  let mean = 0;
  for (const h of hs) mean += h;
  mean /= hs.length;
  let v = 0;
  for (const h of hs) v += (h - mean) * (h - mean);
  return { mean, rough: Math.sqrt(v / hs.length) };
}

const cache = new Map<BodyId, MissionSites>();

export function computeSites(def: BodyDef): MissionSites {
  const hit = cache.get(def.id);
  if (hit) return hit;
  const gen = new SurfaceGenerator(def); // base heights only (no clearings)
  const p = prefsFor(def);
  const sun = sunDirFor(def);
  // 1) Coarse candidates on a cube grid (arithmetic only).
  const G = 22;
  let best: { n: V3; score: number } | null = null;
  const d: number[] = [0, 0, 0];
  for (let face = 0; face < 6; face++) {
    for (let j = 0; j < G; j++) {
      for (let i = 0; i < G; i++) {
        faceDir(face, -1 + (2 * (i + 0.5)) / G, -1 + (2 * (j + 0.5)) / G, d);
        const n: V3 = [d[0], d[1], d[2]];
        const sd = dot(n, sun);
        if (sd < p.sunLo || sd > p.sunHi) continue;
        if (p.face && dot(n, p.face) < p.faceMin) continue;
        gen.baseInfo(n[0], n[1], n[2], info);
        if (info.biome < p.biomeLo || info.biome > p.biomeHi) continue;
        const f = flatness(gen, n, 120);
        const sunMid = (p.sunLo + p.sunHi) / 2;
        const score = -f.rough - Math.abs(sd - sunMid) * 30 - info.rockiness * 20;
        if (!best || score > best.score) best = { n, score };
      }
    }
  }
  if (!best) throw new Error(`No mission site candidate for ${def.id}`);
  // 2) Local refinement within ~2 km for the flattest spot.
  const basis0 = tangentBasis(best.n);
  let landing = best.n;
  let lf = flatness(gen, landing, 120);
  for (const dist of [450, 900, 1400]) {
    for (const [c, s] of BEARINGS) {
      const cand = offsetDir(best.n, basis0, c, s, dist, gen.R);
      const sd = dot(cand, sun);
      if (sd < p.sunLo || sd > p.sunHi) continue;
      gen.baseInfo(cand[0], cand[1], cand[2], info);
      if (info.biome < p.biomeLo || info.biome > p.biomeHi) continue;
      const f = flatness(gen, cand, 120);
      if (f.rough < lf.rough * 0.9) {
        landing = cand;
        lf = f;
      }
    }
  }
  // 3) Relay pad ~190 m away on the flattest bearing.
  const lb = tangentBasis(landing);
  let relay: V3 = offsetDir(landing, lb, 1, 0, RELAY_DISTANCE, gen.R);
  let relayScore = Infinity;
  let relayMean = 0;
  for (const [c, s] of BEARINGS) {
    const cand = offsetDir(landing, lb, c, s, RELAY_DISTANCE, gen.R);
    const f = flatness(gen, cand, 25);
    const score = f.rough * 3 + Math.abs(f.mean - lf.mean) * 0.15;
    if (score < relayScore) {
      relayScore = score;
      relay = cand;
      relayMean = f.mean;
    }
  }
  const clearings: Clearing[] = [
    { dir: landing, height: lf.mean, r0: LANDING_R0, r1: LANDING_R1 },
    { dir: relay, height: relayMean, r0: RELAY_R0, r1: RELAY_R1 },
  ];
  // 4) Three sample sites around the relay pad.
  const rb = tangentBasis(relay);
  const rot = hashCombine(def.seed, 'samples') % 8;
  const samples: SampleSite[] = [];
  const dists = [26, 40, 54];
  for (let i = 0; i < 3; i++) {
    const [c, s] = BEARINGS[(rot + i * 3) % 8];
    samples.push({ id: `${def.id}:sample:${i}`, dir: offsetDir(relay, rb, c, s, dists[i], gen.R) });
  }
  const sites: MissionSites = {
    bodyId: def.id,
    landing: { dir: landing, height: lf.mean },
    relay: { id: `${def.id}:relay`, dir: relay, height: relayMean },
    samples,
    clearings,
  };
  cache.set(def.id, sites);
  return sites;
}
