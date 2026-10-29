import { describe, expect, it } from 'vitest';
import { Frustum, Matrix4, PerspectiveCamera, Vector3 } from 'three';
import { BODIES, BODY_IDS } from '../src/world/bodies';
import { FACES, gridDir, gridResolution, dirToFace, chunkAt } from '../src/world/cube';
import { getSurface, SurfaceGenerator, type SurfaceInfo } from '../src/world/surface';
import { computeSites } from '../src/world/sites';
import { generateChunk, GRID_VERTS, makeChunkIndex, VERT_COUNT } from '../src/terrain/chunkGen';
import { ChunkStore } from '../src/terrain/ChunkStore';
import { TerrainManager, horizonCulled, type TNode, type TerrainView } from '../src/terrain/TerrainManager';
import { createTerrainMaterials, makeTerrainUniforms } from '../src/terrain/terrainMaterial';
import { FakeBackend } from './fakeBackend';
import { mulberry32 } from '../src/core/rng';
import { DataTexture } from 'three';

const ilex = BODIES.ilex;

describe('cube-sphere parameterization', () => {
  it('shares bit-identical directions on all 12 edges and 8 corners', () => {
    // Collect border directions for each face at an intermediate level and
    // count in how many faces each exact direction occurs.
    const maxLevel = ilex.maxLevel;
    const M = gridResolution(maxLevel);
    const step = 2 ** (maxLevel - 3); // level-3 vertex spacing
    const counts = new Map<string, number>();
    const d = [0, 0, 0];
    for (let f = 0; f < 6; f++) {
      const seen = new Set<string>();
      for (let k = 0; k <= M; k += step) {
        for (const [gi, gj] of [[0, k], [M, k], [k, 0], [k, M]]) {
          gridDir(f, gi, gj, M, d);
          const key = `${d[0]},${d[1]},${d[2]}`;
          if (seen.has(key)) continue;
          seen.add(key);
          counts.set(key, (counts.get(key) ?? 0) + 1);
        }
      }
    }
    let edges = 0;
    let corners = 0;
    for (const c of counts.values()) {
      expect(c).toBeGreaterThanOrEqual(2); // every border vertex is shared exactly
      if (c === 2) edges++;
      if (c === 3) corners++;
    }
    expect(corners).toBe(8);
    expect(edges).toBe(12 * (M / step - 1));
  });

  it('maps directions back to their face coordinates', () => {
    const rnd = mulberry32(3);
    const d = [0, 0, 0];
    for (let i = 0; i < 500; i++) {
      const f = Math.floor(rnd() * 6);
      const u = rnd() * 1.98 - 0.99;
      const v = rnd() * 1.98 - 0.99;
      const M = 1 << 20;
      gridDir(f, ((u + 1) / 2) * M, ((v + 1) / 2) * M, M, d);
      const r = dirToFace(d[0], d[1], d[2]);
      expect(r.face).toBe(f);
      expect(Math.abs(r.u - u)).toBeLessThan(1e-9);
      expect(Math.abs(r.v - v)).toBeLessThan(1e-9);
    }
    expect(FACES.length).toBe(6);
  });
});

describe('surface generator', () => {
  it('is deterministic and bounded for every body', () => {
    const rnd = mulberry32(11);
    for (const id of BODY_IDS) {
      const def = BODIES[id];
      const a = new SurfaceGenerator(def);
      const b = new SurfaceGenerator(def);
      const ia: SurfaceInfo = { height: 0, biome: 0, variation: 0, special: 0, rockiness: 0 };
      const ib: SurfaceInfo = { ...ia };
      for (let i = 0; i < 2000; i++) {
        const v = new Vector3(rnd() * 2 - 1, rnd() * 2 - 1, rnd() * 2 - 1).normalize();
        a.info(v.x, v.y, v.z, ia);
        b.info(v.x, v.y, v.z, ib);
        expect(ia).toEqual(ib);
        expect(ia.height).toBeGreaterThanOrEqual(0);
        expect(ia.height).toBeLessThanOrEqual(def.maxHeight);
      }
    }
  });

  it('places mission sites deterministically with flat clearings and samples nearby', () => {
    for (const id of BODY_IDS) {
      const def = BODIES[id];
      const s = computeSites(def);
      const gen = getSurface(def, s.clearings);
      const l = s.landing.dir;
      // Landing clearing is flat (constant radius) within r0.
      const h0 = gen.height(l[0], l[1], l[2]);
      expect(Math.abs(h0 - s.landing.height)).toBeLessThan(1e-6);
      const rel = s.relay.dir;
      const distRelay = Math.hypot(rel[0] - l[0], rel[1] - l[1], rel[2] - l[2]) * def.radius;
      expect(distRelay).toBeGreaterThan(150);
      expect(distRelay).toBeLessThan(260);
      for (const smp of s.samples) {
        const ds = Math.hypot(smp.dir[0] - rel[0], smp.dir[1] - rel[1], smp.dir[2] - rel[2]) * def.radius;
        expect(ds).toBeGreaterThan(20);
        expect(ds).toBeLessThan(60);
      }
    }
  });
});

// The original body plus the generators added in the studio round (Orrin, Saro).
for (const def of [ilex, BODIES.orrin, BODIES.saro]) describe(`chunk generation (${def.name})`, () => {
  const gen = getSurface(def, computeSites(def).clearings);

  it('produces identical data regardless of job order or revisits', () => {
    const a = generateChunk(def, gen, 2, 5, 11, 7, 1);
    generateChunk(def, gen, 0, 3, 1, 2, 1);
    generateChunk(def, gen, 4, 6, 40, 3, 1);
    const fresh = new SurfaceGenerator(def);
    fresh.clearings = computeSites(def).clearings;
    const b = generateChunk(def, fresh, 2, 5, 11, 7, 1);
    expect(Array.from(b.positions)).toEqual(Array.from(a.positions));
    expect(Array.from(b.normals)).toEqual(Array.from(a.normals));
    expect(Array.from(b.attrs)).toEqual(Array.from(a.attrs));
    expect(b.center).toEqual(a.center);
  });

  it('agrees on shared vertices and normals across a cube-face edge', () => {
    // Pick a direction on the +X/+Z edge and generate the two adjacent chunks.
    const level = def.maxLevel - 2;
    const M = gridResolution(def.maxLevel);
    const d = [0, 0, 0];
    gridDir(0, 0, M / 2 + 1000, M, d); // +X face, u = -1 edge (z = +1)
    const fa = dirToFace(d[0] + 1e-9, d[1], d[2] - 1e-9); // nudge into +X
    const fb = dirToFace(d[0] - 1e-9, d[1], d[2] + 1e-9); // nudge into +Z
    expect(fa.face).toBe(0);
    expect(fb.face).toBe(4);
    const ca = chunkAt(fa.face, fa.u, fa.v, level);
    const cb = chunkAt(fb.face, fb.u, fb.v, level);
    const A = generateChunk(def, gen, fa.face, level, ca.x, ca.y, 1);
    const B = generateChunk(def, gen, fb.face, level, cb.x, cb.y, 1);
    const world = (c: typeof A, i: number) =>
      new Vector3(c.center[0] + c.positions[i * 3], c.center[1] + c.positions[i * 3 + 1], c.center[2] + c.positions[i * 3 + 2]);
    let matched = 0;
    for (let i = 0; i < GRID_VERTS; i++) {
      const pa = world(A, i);
      for (let j = 0; j < GRID_VERTS; j++) {
        const pb = world(B, j);
        if (pa.distanceTo(pb) < 0.01) {
          matched++;
          const na = new Vector3(A.normals[i * 3], A.normals[i * 3 + 1], A.normals[i * 3 + 2]);
          const nb = new Vector3(B.normals[j * 3], B.normals[j * 3 + 1], B.normals[j * 3 + 2]);
          expect(na.angleTo(nb)).toBeLessThan(1e-4);
        }
      }
    }
    // A shared edge has 33 vertices at the same level.
    expect(matched).toBe(33);
  });

  it('builds a consistent index buffer (grid then outward skirts)', () => {
    const idx = makeChunkIndex();
    expect(idx.length).toBe(32 * 32 * 6 + 4 * 32 * 6);
    let max = 0;
    for (const i of idx) max = Math.max(max, i);
    expect(max).toBe(VERT_COUNT - 1);
  });

  it('places morph targets on the parent surface (odd vertices interpolate even ones)', () => {
    const c = generateChunk(def, gen, 3, 6, 21, 40, 1);
    // Even/even vertices do not move.
    for (let j = 0; j < 33; j += 2) for (let i = 0; i < 33; i += 2) {
      const g = j * 33 + i;
      expect(Math.hypot(c.morphDelta[g * 3], c.morphDelta[g * 3 + 1], c.morphDelta[g * 3 + 2])).toBe(0);
    }
    expect(c.ownError).toBeGreaterThan(0);
  });
});

function makeView(cam: Vector3, look: Vector3, def = ilex): TerrainView {
  const camera = new PerspectiveCamera(70, 16 / 9, 0.5, 4e5);
  // Local frame == planet frame for the test (planet at the local origin).
  camera.position.copy(cam);
  camera.up.copy(cam).normalize();
  camera.lookAt(look);
  camera.updateMatrixWorld();
  const fr = new Frustum().setFromProjectionMatrix(new Matrix4().multiplyMatrices(camera.projectionMatrix, camera.matrixWorldInverse));
  void def;
  return {
    camPlanet: cam.clone(),
    frustum: fr,
    planetLocal: new Vector3(),
    fovY: (70 * Math.PI) / 180,
    viewportH: 720,
    focusPlanet: cam.clone().multiplyScalar(0.999),
    contactRadius: 150,
  };
}

function checkInvariants(tm: TerrainManager): { leaves: number } {
  const leaves: TNode[] = [];
  const walk = (n: TNode) => (n.isLeaf ? leaves.push(n) : n.children!.forEach(walk));
  tm.roots.forEach(walk);
  const rendered = new Set<string>();
  tm.forEachMeshNode((n) => rendered.add(n.key));
  // Coverage + no overlap: rendered set is exactly the leaf set.
  for (const l of leaves) expect(rendered.has(l.key), `leaf ${l.key} has no mesh`).toBe(true);
  expect(rendered.size).toBe(leaves.length);
  // Right body/token only.
  tm.forEachMeshNode((n) => expect(n.data!.bodyId).toBe(tm.def.id));
  // 2:1 balance across faces at all times.
  const nbFn = (tm as unknown as { neighborLeaves(n: TNode, k: number, o: TNode[]): TNode[] }).neighborLeaves.bind(tm);
  for (const l of leaves) for (const m of nbFn(l, 4, [])) expect(Math.abs(m.level - l.level), `${l.key} vs ${m.key}`).toBeLessThanOrEqual(1);
  return { leaves: leaves.length };
}

describe('quadtree LOD under delayed and reordered worker results', () => {
  it('keeps full coverage, 2:1 balance and no overlap while descending and traveling', () => {
    const def = ilex;
    const backend = new FakeBackend(4, true, 99);
    const store = new ChunkStore(backend, def.id);
    store.maxInFlight = 3;
    const tex = new DataTexture(new Uint8Array(4), 1, 1);
    const mats = createTerrainMaterials(makeTerrainUniforms(tex), 3, true);
    const tm = new TerrainManager(def, store, mats);
    tm.horizonCulling = true;
    const site = new Vector3(...computeSites(def).landing.dir);
    const side = new Vector3(0, 1, 0).cross(site).normalize();
    let maxLevelSeen = 0;
    let tokenSwitched = false;
    for (let it = 0; it < 900; it++) {
      // Descend from 40 km to 60 m, then travel 6 km along the surface.
      const t = Math.min(1, it / 500);
      const alt = 40000 * Math.pow(1 - t, 3) + 60;
      const along = it > 500 ? ((it - 500) / 400) * 6000 : 0;
      const dir = site.clone().addScaledVector(side, along / def.radius).normalize();
      const ground = def.radius + getSurface(def).height(dir.x, dir.y, dir.z);
      const cam = dir.clone().multiplyScalar(ground + alt);
      const look = cam.clone().addScaledVector(side, 1000).addScaledVector(dir, -alt * 0.5);
      tm.update(makeView(cam, look));
      backend.tick();
      tm.updateMorphs(0.05);
      if (it === 300 && !tokenSwitched) {
        // Body switch round-trip: in-flight results with the old token must be discarded.
        store.setBody('vesper');
        store.setBody('ilex');
        tokenSwitched = true;
      }
      if (tm.coarseReady && it > 5) checkInvariants(tm);
      maxLevelSeen = Math.max(maxLevelSeen, tm.stats.maxLevel);
    }
    // Balance: no neighboring leaves more than one level apart.
    const leaves: TNode[] = [];
    const walk = (n: TNode) => (n.isLeaf ? leaves.push(n) : n.children!.forEach(walk));
    tm.roots.forEach(walk);
    for (const l of leaves) {
      const nb = (tm as unknown as { neighborLeaves(n: TNode, k: number, o: TNode[]): TNode[] }).neighborLeaves(l, 4, []);
      for (const m of nb) expect(Math.abs(m.level - l.level)).toBeLessThanOrEqual(1);
    }
    expect(maxLevelSeen).toBe(def.maxLevel);
    expect(store.discarded).toBeGreaterThanOrEqual(0);
    expect(store.cacheBytes).toBeLessThanOrEqual(64 * 1024 * 1024);
  }, 240_000);
});

describe('horizon culling', () => {
  it('never culls a sphere that has a visible point (conservative)', () => {
    const rnd = mulberry32(5);
    const R = ilex.radius;
    const Ro = R * 0.999;
    let culledCount = 0;
    for (let i = 0; i < 4000; i++) {
      const e = new Vector3(rnd() * 2 - 1, rnd() * 2 - 1, rnd() * 2 - 1).normalize().multiplyScalar(R + 50 + rnd() * 60000);
      const c = new Vector3(rnd() * 2 - 1, rnd() * 2 - 1, rnd() * 2 - 1).normalize().multiplyScalar(R + rnd() * 900);
      const r = 20 + rnd() * 3000;
      if (!horizonCulled(c.x, c.y, c.z, r, e, Ro)) continue;
      culledCount++;
      // Every sampled point of the sphere must be hidden behind the occluder.
      for (let k = 0; k < 40; k++) {
        const p = new Vector3(rnd() * 2 - 1, rnd() * 2 - 1, rnd() * 2 - 1).normalize().multiplyScalar(r * Math.cbrt(rnd())).add(c);
        const dir = p.clone().sub(e);
        const L = dir.length();
        dir.divideScalar(L);
        const b = e.dot(dir);
        const cc = e.lengthSq() - Ro * Ro;
        const disc = b * b - cc;
        expect(disc).toBeGreaterThan(0);
        const tNear = -b - Math.sqrt(disc);
        expect(tNear).toBeGreaterThan(0);
        expect(tNear).toBeLessThan(L);
      }
    }
    expect(culledCount).toBeGreaterThan(50);
  });
});
