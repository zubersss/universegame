import { describe, expect, it } from 'vitest';
import { createHash } from 'node:crypto';
import { Vector3 } from 'three';
import { generateChunk } from '../src/terrain/chunkGen';
import { BODIES, BODY_IDS, CORE_BODY_IDS, EXTENDED_BODY_IDS, SUN_DIR, isBodyId, type BodyId } from '../src/world/bodies';
import { getSurface, SurfaceGenerator, type SurfaceInfo } from '../src/world/surface';
import { computeSites, seamDistance, tangentBasis, offsetDir } from '../src/world/sites';
import { CruiseController, safetyRadius, type CruiseInput } from '../src/ship/Cruise';
import { SIM_DT } from '../src/game/config';
import { quatFromForwardUp } from '../src/core/mathx';

// Locks the system layout and the new worlds (Orrin, Saro): placement against
// every body, day-side walkable mission sites clear of tile seams, honest
// height bounds, cruise legs comparable to the original three-body routes, and
// unchanged generators and sites for the original bodies.

const NEW_BODIES: BodyId[] = ['orrin', 'saro'];

function center(id: BodyId): Vector3 {
  const c = BODIES[id].center;
  return new Vector3(c[0], c[1], c[2]);
}

/** Smallest clearance of the straight segment a→b from any third body's safety sphere. */
function lineClearance(a: BodyId, b: BodyId): number {
  const pa = center(a);
  const ab = center(b).sub(pa);
  let m = Infinity;
  for (const k of BODY_IDS) {
    if (k === a || k === b) continue;
    const t = Math.max(0, Math.min(1, center(k).sub(pa).dot(ab) / ab.lengthSq()));
    const p = pa.clone().addScaledVector(ab, t);
    m = Math.min(m, p.distanceTo(center(k)) - safetyRadius(BODIES[k]));
  }
  return m;
}

const IDLE: CruiseInput = { pitch: 0, yaw: 0, roll: 0, throttle: 1, brake: false, toggleOff: false };

/** Simulated cruise time from just outside a's envelope toward b until the automatic hand-back. */
function cruiseLeg(a: BodyId, b: BodyId): { time: number; exit: string | null; stops: number } {
  const dir = center(b).sub(center(a)).normalize();
  const start = center(a).addScaledVector(dir, safetyRadius(BODIES[a]) + 6000);
  const up = Math.abs(dir.y) > 0.9 ? new Vector3(1, 0, 0) : new Vector3(0, 1, 0);
  const c = new CruiseController();
  c.begin(start, quatFromForwardUp(dir, up), new Vector3());
  let exit: string | null = null;
  let t = 0;
  for (let i = 0; i < 60 * 600 && !exit; i++) {
    exit = c.step(SIM_DT, IDLE).exit;
    t += SIM_DT;
  }
  return { time: t, exit, stops: c.safetyStops };
}

const sun = SUN_DIR as unknown as number[];
const dot = (a: readonly number[], b: readonly number[]) => a[0] * b[0] + a[1] * b[1] + a[2] * b[2];

/** Steepest slope (degrees) of the final surface within radius r of dir. */
function maxSlopeDeg(gen: SurfaceGenerator, dir: [number, number, number], r: number): number {
  const basis = tangentBasis(dir);
  let worst = 0;
  const step = 2;
  for (let k = 0; k < 8; k++) {
    const a = (k / 8) * Math.PI * 2;
    for (const dist of [0, r * 0.5, r]) {
      const p = offsetDir(dir, basis, Math.cos(a), Math.sin(a), dist, gen.R);
      const pb = tangentBasis(p);
      const h0 = gen.height(p[0], p[1], p[2]);
      for (const [c, s] of [[1, 0], [0, 1]]) {
        const q = offsetDir(p, pb, c, s, step, gen.R);
        const g = Math.abs(gen.height(q[0], q[1], q[2]) - h0) / step;
        worst = Math.max(worst, (Math.atan(g) * 180) / Math.PI);
      }
    }
  }
  return worst;
}

describe('system layout', () => {
  it('lists every body once, in navigation order, split into the core and extended surveys', () => {
    expect(BODY_IDS).toEqual(['ilex', 'vesper', 'cairn', 'orrin', 'saro']);
    BODY_IDS.forEach((id, i) => {
      expect(BODIES[id].id).toBe(id);
      expect(BODIES[id].index).toBe(i);
      expect(isBodyId(id)).toBe(true);
    });
    expect(isBodyId('nowhere')).toBe(false);
    expect(isBodyId(3)).toBe(false);
    expect(CORE_BODY_IDS).toEqual(['ilex', 'vesper', 'cairn']);
    expect(EXTENDED_BODY_IDS).toEqual(NEW_BODIES);
    expect(new Set(BODY_IDS.map((id) => BODIES[id].seed)).size).toBe(BODY_IDS.length);
  });

  it('keeps every centre at least 500 km from every other and the safety spheres apart', () => {
    for (let i = 0; i < BODY_IDS.length; i++) {
      for (let j = i + 1; j < BODY_IDS.length; j++) {
        const a = BODY_IDS[i];
        const b = BODY_IDS[j];
        const d = center(a).distanceTo(center(b));
        expect(d, `${a}-${b}`).toBeGreaterThanOrEqual(500000);
        expect(d - safetyRadius(BODIES[a]) - safetyRadius(BODIES[b]), `${a}-${b} gap`).toBeGreaterThan(300000);
      }
    }
  });

  it('keeps every straight body-to-body line clear of third bodies\' safety spheres', () => {
    for (let i = 0; i < BODY_IDS.length; i++) {
      for (let j = i + 1; j < BODY_IDS.length; j++) {
        expect(lineClearance(BODY_IDS[i], BODY_IDS[j]), `${BODY_IDS[i]}-${BODY_IDS[j]}`).toBeGreaterThan(20000);
      }
    }
  });

  it('makes cruise legs from Ilex to the new worlds comparable to Ilex → Vesper', () => {
    const ref = cruiseLeg('ilex', 'vesper');
    expect(ref.exit).toBe('approach');
    for (const b of NEW_BODIES) {
      const leg = cruiseLeg('ilex', b);
      expect(leg.exit, b).toBe('approach');
      expect(leg.stops, b).toBe(0);
      expect(leg.time / ref.time, b).toBeGreaterThan(0.8);
      expect(leg.time / ref.time, b).toBeLessThan(1.25);
    }
    // The longest leg in the system (Vesper ↔ Orrin, opposite sides of Ilex) stays bounded.
    expect(cruiseLeg('vesper', 'orrin').time).toBeLessThan(ref.time * 2.4);
  });
});

describe('new worlds', () => {
  it('have honest height bounds and finite surface data', () => {
    const info: SurfaceInfo = { height: 0, biome: 0, variation: 0, special: 0, rockiness: 0 };
    for (const id of NEW_BODIES) {
      const def = BODIES[id];
      const gen = new SurfaceGenerator(def);
      let lo = Infinity;
      let hi = -Infinity;
      let s = 12345;
      const rnd = () => ((s = (Math.imul(s, 1103515245) + 12345) >>> 0) / 4294967296) * 2 - 1;
      let biomeA = 0;
      for (let i = 0; i < 20000; i++) {
        const x = rnd(), y = rnd(), z = rnd();
        const l = Math.hypot(x, y, z);
        if (l < 1e-3) continue;
        gen.baseInfo(x / l, y / l, z / l, info);
        for (const v of [info.height, info.biome, info.variation, info.special, info.rockiness]) expect(Number.isFinite(v)).toBe(true);
        for (const v of [info.biome, info.special, info.rockiness]) {
          expect(v).toBeGreaterThanOrEqual(0);
          expect(v).toBeLessThanOrEqual(1);
        }
        if (info.biome < 0.5) biomeA++;
        lo = Math.min(lo, info.height);
        hi = Math.max(hi, info.height);
      }
      // The clamp to [0, maxHeight] must never be what bounds the terrain.
      expect(lo, id).toBeGreaterThan(0);
      expect(hi, id).toBeLessThan(def.maxHeight);
      // Both biomes exist on every world.
      expect(biomeA / 20000, id).toBeGreaterThan(0.1);
      expect(biomeA / 20000, id).toBeLessThan(0.9);
    }
  });

  it('place day-side, walkable mission sites away from tile seams', () => {
    for (const id of NEW_BODIES) {
      const def = BODIES[id];
      const s = computeSites(def);
      const gen = getSurface(def, s.clearings);
      for (const [name, d] of [['landing', s.landing.dir], ['relay', s.relay.dir], ...s.samples.map((x) => [x.id, x.dir])] as [string, [number, number, number]][]) {
        expect(dot(d, sun), `${id} ${name} sun`).toBeGreaterThan(0.25);
        expect(seamDistance(def, d), `${id} ${name} seam`).toBeGreaterThan(1);
      }
      expect(maxSlopeDeg(gen, s.landing.dir, 50), `${id} landing slope`).toBeLessThan(6);
      expect(maxSlopeDeg(gen, s.relay.dir, 8), `${id} relay slope`).toBeLessThan(10);
      for (const smp of s.samples) expect(maxSlopeDeg(gen, smp.dir, 3), smp.id).toBeLessThan(30);
    }
  });
});

describe('new world character', () => {
  const info: SurfaceInfo = { height: 0, biome: 0, variation: 0, special: 0, rockiness: 0 };
  /** Deterministic directions where `pick(info)` holds. */
  function find(gen: SurfaceGenerator, pick: (i: SurfaceInfo) => boolean, count: number): [number, number, number][] {
    const out: [number, number, number][] = [];
    let s = 777;
    const rnd = () => ((s = (Math.imul(s, 1103515245) + 12345) >>> 0) / 4294967296) * 2 - 1;
    for (let k = 0; k < 200000 && out.length < count; k++) {
      const x = rnd(), y = rnd(), z = rnd();
      const l = Math.hypot(x, y, z);
      if (l < 1e-3) continue;
      const d: [number, number, number] = [x / l, y / l, z / l];
      if (pick(gen.baseInfo(d[0], d[1], d[2], info))) out.push(d);
    }
    return out;
  }
  /** Base heights along a straight 1 m-step transect from d. */
  function transect(gen: SurfaceGenerator, d: [number, number, number], len: number): number[] {
    const b = tangentBasis(d);
    const hs: number[] = [];
    for (let m = 0; m <= len; m++) {
      const p = offsetDir(d, b, 1, 0, m, gen.R);
      hs.push(gen.baseInfo(p[0], p[1], p[2], info).height);
    }
    return hs;
  }

  it('Orrin: basalt highlands break into polygonal columns; lowland valleys have flat, wet floors', () => {
    const gen = new SurfaceGenerator(BODIES.orrin);
    const high = find(gen, (i) => i.biome < 0.05, 12);
    expect(high.length).toBe(12);
    for (const d of high) {
      const hs = transect(gen, d, 120);
      let steps = 0;
      for (let i = 1; i < hs.length; i++) if (Math.abs(hs[i] - hs[i - 1]) > 0.4) steps++;
      // Column edges every ~11 m: several distinct steps along 120 m.
      expect(steps).toBeGreaterThanOrEqual(4);
    }
    const floors = find(gen, (i) => i.special > 0.9 && i.biome > 0.95, 12);
    expect(floors.length).toBe(12);
    const ranges: number[] = [];
    for (const d of floors) {
      const hs = transect(gen, d, 40);
      ranges.push(Math.max(...hs) - Math.min(...hs));
      // Walkable on the floor and up the valley wall (< 35° per metre; the walk limit is 45°).
      for (let i = 1; i < hs.length; i++) expect(Math.abs(hs[i] - hs[i - 1])).toBeLessThan(0.7);
    }
    // Most floors are near level over 40 m (fog pools there).
    ranges.sort((a, b) => a - b);
    expect(ranges[Math.floor(ranges.length / 2)]).toBeLessThan(1.5);
  });

  it('Saro: brine pans are level, their rims walkable, and the dry crust is polygonal', () => {
    const gen = new SurfaceGenerator(BODIES.saro);
    for (const d of find(gen, (i) => i.biome > 0.99, 12)) {
      const hs = transect(gen, d, 40);
      expect(Math.max(...hs) - Math.min(...hs)).toBeLessThan(0.6);
    }
    for (const d of find(gen, (i) => i.biome > 0.1 && i.biome < 0.4, 12)) {
      const hs = transect(gen, d, 20);
      for (let i = 1; i < hs.length; i++) expect(Math.abs(hs[i] - hs[i - 1])).toBeLessThan(0.35); // < 20° per metre
    }
    const dry = find(gen, (i) => i.biome < 0.01 && i.rockiness < 0.01, 12);
    expect(dry.length).toBe(12);
    for (const d of dry) {
      const hs = transect(gen, d, 150);
      let peaks = 0;
      for (let i = 1; i < hs.length - 1; i++) if (hs[i] > hs[i - 1] && hs[i] >= hs[i + 1]) peaks++;
      expect(peaks).toBeGreaterThanOrEqual(3); // raised polygon edges
    }
  });
});

describe('original worlds are unchanged', () => {
  const GOLDEN = {"ilex":{"seed":1817459381,"h":[266.61320609924763,143.97461422060906,92.2422721932703,258.6580145649501,214.0121690159732],"landing":{"dir":[0.23527764119475578,-0.23495304853366245,-0.9431020605101923],"height":184.9331622887605},"relay":[0.23545655281206423,-0.23187386466473153,-0.94381922136779]},"vesper":{"seed":2616949894,"h":[92.45723519472672,283.87653353513065,95.40452012565736,115.10389795908523,120.59150562576492],"landing":{"dir":[-0.3810714436110077,-0.9192481395765141,0.09883022184200745],"height":124.19660340491352},"relay":[-0.38382831050133204,-0.9177896206501627,0.10167615396209354]},"cairn":{"seed":3839947091,"h":[298.75281484329497,212.8654883242649,261.66611077758853,215.46108768042285,216.6087160742163],"landing":{"dir":[0.21432724425155084,-0.8395918824604391,-0.4991485783592618],"height":136.91139443283632},"relay":[0.22364568140180746,-0.8354908133981876,-0.5019339696788372]}} as Record<'ilex' | 'vesper' | 'cairn', { seed: number; h: number[]; landing: { dir: number[]; height: number }; relay: number[] }>;
  const DIRS = [[0.3, 0.8, -0.52], [-0.9, 0.1, 0.42], [0.05, -0.99, 0.1], [0.6, 0.6, 0.53], [-0.2, -0.4, -0.89]];
  it('keeps seeds, heights and mission sites bit-identical to the three-body release', () => {
    for (const id of ['ilex', 'vesper', 'cairn'] as const) {
      const def = BODIES[id];
      const g = GOLDEN[id];
      expect(def.seed).toBe(g.seed);
      const s = computeSites(def);
      expect(s.landing.dir).toEqual(g.landing.dir);
      expect(s.landing.height).toBe(g.landing.height);
      expect(s.relay.dir).toEqual(g.relay);
      const gen = getSurface(def, s.clearings);
      DIRS.forEach((d, i) => {
        const l = Math.hypot(d[0], d[1], d[2]);
        expect(gen.height(d[0] / l, d[1] / l, d[2] / l)).toBe(g.h[i]);
      });
    }
  });

  // Hashes of chunk positions, normals, morph deltas, morph normals (xyz), tiling and
  // material attributes from the three-body release. The concavity byte (morphNormal.w)
  // is new data for the material and is excluded.
  const CHUNKS: Record<string, string> = {"ilex:2/5/11/7":"0aecc1fc650304fb074f69d4","ilex:0/0/0/0":"29c348bc057177140fc024f1","ilex:4/10/300/410":"2403a4efc221afedcc8be39e","vesper:2/5/11/7":"2b5f1b0bf76af7fc5d0def56","vesper:0/0/0/0":"34d874c8f09a7824f72decee","vesper:4/10/300/410":"97da3d80cef1e8eff99c5231","cairn:2/5/11/7":"fff920b0ad7dd3a9858431a5","cairn:0/0/0/0":"bc59132a90d0b147e46ac91d","cairn:4/9/300/410":"4de99fd347a4dd8de9dd6d95"};
  it('keeps chunk geometry and attributes identical (concavity byte aside)', () => {
    for (const id of ['ilex', 'vesper', 'cairn'] as const) {
      const def = BODIES[id];
      const gen = getSurface(def, computeSites(def).clearings);
      for (const [f, l, x, y] of [[2, 5, 11, 7], [0, 0, 0, 0], [4, def.maxLevel, 300, 410]]) {
        const c = generateChunk(def, gen, f, l, x, y, 1);
        const xyz = c.morphNormal.filter((_, i) => i % 4 !== 3);
        const h = createHash('sha256');
        for (const a of [c.positions, c.normals, c.morphDelta, xyz, c.tile, c.attrs]) h.update(Buffer.from(a.buffer, a.byteOffset, a.byteLength));
        expect(h.digest('hex').slice(0, 24), `${id}:${c.key}`).toBe(CHUNKS[`${id}:${c.key}`]);
      }
    }
  });

  it('writes a bounded, signed concavity byte that marks hollows and crests', () => {
    const def = BODIES.cairn; // craters: clear hollows and rims
    const gen = getSurface(def, computeSites(def).clearings);
    const c = generateChunk(def, gen, 2, 6, 20, 30, 1);
    let pos = 0;
    let neg = 0;
    for (let i = 3; i < c.morphNormal.length; i += 4) {
      const w = c.morphNormal[i];
      expect(Math.abs(w)).toBeLessThanOrEqual(127);
      if (w > 4) pos++;
      if (w < -4) neg++;
    }
    expect(pos).toBeGreaterThan(0);
    expect(neg).toBeGreaterThan(0);
  });
});
