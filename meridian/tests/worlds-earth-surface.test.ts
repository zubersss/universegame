// W4: the data-backed Earth surface generator — determinism, seed independence
// of the coastline, continuity (raster cells, ±180° seam, poles, cube faces),
// worker-order independence, and proxy (level-0 roots) to surface continuity
// on one region (New Zealand's Southern Alps, Tasman coast to Aoraki).
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { beforeAll, describe, expect, it } from 'vitest';
import { BODIES, type BodyDef } from '../src/world/bodies';
import { installEarthData, latLonOf, loadEarthData, sampleBilinear, sampleCubic, type EarthRasters } from '../src/world/earthData';
import { SurfaceGenerator, bodyDataReady, ensureBodyData, newSurfaceInfo } from '../src/world/surface';
import { computeSites } from '../src/world/sites';
import { chunkAt, dirToFace, gridDir, gridResolution } from '../src/world/cube';
import { generateChunk } from '../src/terrain/chunkGen';
import { mulberry32 } from '../src/core/rng';
import { EARTH_INFILL_MAX_M, dirToGeo, earthElevationM, geoToDir, subsolarPoint } from '../src/world/geo';

const earth = BODIES.earth;
const sea = earth.seaLevel!;
let E: EarthRasters;

beforeAll(async () => {
  const dir = fileURLToPath(new URL('../src/data/earth/', import.meta.url));
  E = await loadEarthData(async (_name, _url, file) => readFileSync(dir + file));
  installEarthData(E);
});

/** Unit direction (system frame) of a latitude/longitude in Earth's body frame. */
function dirOf(lat: number, lon: number): [number, number, number] {
  const f = earth.frame;
  const a = (lat * Math.PI) / 180;
  const o = (lon * Math.PI) / 180;
  const c = Math.cos(a);
  const v = [0, 1, 2].map((k) => c * Math.cos(o) * f.meridian[k] + c * Math.sin(o) * f.east[k] + Math.sin(a) * f.north[k]);
  const l = Math.hypot(v[0], v[1], v[2]);
  return [v[0] / l, v[1] / l, v[2] / l];
}

function randomDir(rnd: () => number): [number, number, number] {
  for (;;) {
    const x = rnd() * 2 - 1;
    const y = rnd() * 2 - 1;
    const z = rnd() * 2 - 1;
    const l = Math.hypot(x, y, z);
    if (l > 0.1 && l <= 1) return [x / l, y / l, z / l];
  }
}

describe('Earth frame and data readiness', () => {
  it('maps directions to latitude/longitude consistently with the body frame', async () => {
    await ensureBodyData(earth);
    expect(bodyDataReady(earth)).toBe(true);
    expect(bodyDataReady(BODIES.ilex)).toBe(true);
    const f = earth.frame;
    expect(f.tag).toBe('measured');
    expect(Math.hypot(...f.north)).toBeCloseTo(1, 12);
    expect(f.north[0] * f.meridian[0] + f.north[1] * f.meridian[1] + f.north[2] * f.meridian[2]).toBeCloseTo(0, 12);
    // Obliquity: Earth's pole is 23.44° from the ecliptic pole (system +Y).
    expect((Math.acos(f.north[1]) * 180) / Math.PI).toBeCloseTo(23.44, 1);
    const ll = { lat: 0, lon: 0 };
    for (const [lat, lon] of [[27.99, 86.93], [-43.6, 170.14], [0, 179.999], [0, -179.999], [89.9, 10], [-89.9, -120], [51.5, -0.1]]) {
      const d = dirOf(lat, lon);
      latLonOf(d[0], d[1], d[2], f.north, f.meridian, f.east, ll);
      expect(ll.lat).toBeCloseTo(lat, 9);
      expect(ll.lon).toBeCloseTo(lon, 9);
    }
    // At EPOCH (1 January, 00:00 TDB) the Sun stands over the South Pacific near the date line.
    const s = [-earth.center[0], -earth.center[1], -earth.center[2]];
    const sl = Math.hypot(s[0], s[1], s[2]);
    latLonOf(s[0] / sl, s[1] / sl, s[2] / sl, f.north, f.meridian, f.east, ll);
    expect(ll.lat).toBeCloseTo(-23.0, 0);
    expect(Math.abs(ll.lon)).toBeGreaterThan(177);
  });
});

describe('Earth surface generator (W4)', () => {
  it('is deterministic and bounded', () => {
    const a = new SurfaceGenerator(earth);
    const b = new SurfaceGenerator(earth);
    const ia = newSurfaceInfo();
    const ib = newSurfaceInfo();
    const rnd = mulberry32(5);
    for (let i = 0; i < 4000; i++) {
      const d = randomDir(rnd);
      a.info(d[0], d[1], d[2], ia);
      b.info(d[0], d[1], d[2], ib);
      expect(ia).toEqual(ib);
      expect(ia.height).toBeGreaterThanOrEqual(0);
      expect(ia.height).toBeLessThanOrEqual(earth.maxHeight);
      expect(ia.hazard).toBe(0);
      for (const k of ['biome', 'variation', 'special', 'rockiness'] as const) {
        expect(ia[k]).toBeGreaterThanOrEqual(0);
        expect(ia[k]).toBeLessThanOrEqual(1);
      }
    }
  });

  it('never moves a coastline when the seed changes', () => {
    const other: BodyDef = { ...earth, seed: (earth.seed ^ 0x5bd1e995) >>> 0 };
    const a = new SurfaceGenerator(earth);
    const b = new SurfaceGenerator(other);
    const ia = newSurfaceInfo();
    const ib = newSurfaceInfo();
    const ll = { lat: 0, lon: 0 };
    const cs = { v: 0, dLon: 0, dLat: 0 };
    const f = earth.frame;
    const rnd = mulberry32(17);
    let differ = 0;
    let coastal = 0;
    for (let i = 0; i < 40000; i++) {
      // Half the samples within ~40 km (real) of a shore, where infill would matter.
      let d = randomDir(rnd);
      if (i % 2) {
        for (let t = 0; t < 50; t++) {
          latLonOf(d[0], d[1], d[2], f.north, f.meridian, f.east, ll);
          if (Math.abs(sampleCubic(E.coast, ll.lat, ll.lon, cs).v) < 40) break;
          d = randomDir(rnd);
        }
      }
      a.info(d[0], d[1], d[2], ia);
      b.info(d[0], d[1], d[2], ib);
      latLonOf(d[0], d[1], d[2], f.north, f.meridian, f.east, ll);
      // The generator reads the coastline field through the same cubic sampler.
      const shore = sampleCubic(E.coast, ll.lat, ll.lon, cs).v;
      if (Math.abs(shore) < 40) coastal++;
      // Wet exactly where the coastline data says water, for both seeds.
      expect(ia.liquidLevel != null).toBe(shore < 0);
      expect(ib.liquidLevel != null).toBe(shore < 0);
      if (ia.liquidLevel != null) {
        expect(ia.height).toBeLessThan(ia.liquidLevel);
        expect(ib.height).toBeLessThan(ib.liquidLevel!);
      } else if (sampleBilinear(E.water, ll.lat, ll.lon) === 0) {
        // Dry ground next to the ocean is never below sea level.
        expect(ia.height).toBeGreaterThanOrEqual(sea);
        expect(ib.height).toBeGreaterThanOrEqual(sea);
      }
      if (ia.height !== ib.height) differ++;
    }
    expect(coastal).toBeGreaterThan(15000);
    expect(differ).toBeGreaterThan(25000); // the seed does drive the infill
  });

  it('puts real places where they belong', () => {
    const g = new SurfaceGenerator(earth);
    const info = newSurfaceInfo();
    const at = (lat: number, lon: number) => {
      const d = dirOf(lat, lon);
      return { ...g.info(d[0], d[1], d[2], info) };
    };
    expect(at(27.99, 86.93).height).toBeGreaterThan(sea + 700); // Everest region
    expect(at(32, 88).height).toBeGreaterThan(sea + 600); // Tibetan Plateau
    const ch = at(11.35, 142.2); // Challenger Deep: deep (compressed) ocean
    expect(ch.liquidLevel).toBe(sea);
    expect(ch.height).toBeLessThan(sea - 250);
    const amazon = at(-3, -60);
    expect(amazon.liquidLevel).toBeNull();
    expect(amazon.height).toBeGreaterThan(sea);
    expect(amazon.height).toBeLessThan(sea + 120);
    expect(amazon.biome).toBeGreaterThan(0.8); // vegetated
    expect(at(23, 10).biome).toBeLessThan(0.3); // Sahara: bare
    expect(at(75, -40).special).toBeGreaterThan(0.6); // Greenland ice
    expect(at(-89.5, 0).special).toBeGreaterThan(0.6); // Antarctic ice
    expect(at(0, -30).liquidLevel).toBe(sea); // Atlantic
    const victoria = at(-1, 33);
    expect(victoria.liquidLevel).toBeGreaterThan(sea + 100); // a lake well above sea level
    expect(victoria.height).toBeLessThan(victoria.liquidLevel!);
  });

  it('raises the Southern Alps from the regional grid: Aoraki a snowy summit above its valleys', () => {
    const g = new SurfaceGenerator(earth);
    const info = newSurfaceInfo();
    const at = (lat: number, lon: number) => {
      const d = dirOf(lat, lon);
      return { ...g.info(d[0], d[1], d[2], info) };
    };
    const aoraki = at(-43.595, 170.142);
    // Higher than everything 5 km (real) around it, and well above Mount Cook Village.
    for (let k = 0; k < 8; k++) {
      const a = (k / 8) * 2 * Math.PI;
      expect(at(-43.595 + 0.045 * Math.sin(a), 170.142 + 0.062 * Math.cos(a)).height, `ring ${k}`).toBeLessThan(aoraki.height - 40);
    }
    expect(aoraki.height - at(-43.735, 170.096).height).toBeGreaterThan(120);
    // Snow on the summit (glaciated cells lower the snow line), none on the coastal plain.
    expect(aoraki.special).toBeGreaterThan(0.8);
    expect(at(-42.75, 171.0).special).toBe(0);
    // Steep but not needles: few slopes above 70 degrees (2 m baselines across the region).
    const R = earth.radius;
    let n = 0;
    let steep = 0;
    for (let lat = -43.9; lat <= -42.6; lat += 0.05) {
      for (let lon = 169.6; lon <= 171.4; lon += 0.06) {
        const d0 = dirOf(lat, lon);
        const dN = dirOf(lat + 2 / ((R * Math.PI) / 180), lon);
        const dE = dirOf(lat, lon + 2 / (((R * Math.PI) / 180) * Math.cos((lat * Math.PI) / 180)));
        const h0 = g.height(d0[0], d0[1], d0[2]);
        const s = Math.hypot(g.height(dN[0], dN[1], dN[2]) - h0, g.height(dE[0], dE[1], dE[2]) - h0) / 2;
        n++;
        if (s > Math.tan((70 * Math.PI) / 180)) steep++;
      }
    }
    expect(steep / n).toBeLessThan(0.02);
  });

  it('is continuous in space, across the ±180° seam and around the poles', () => {
    const g = new SurfaceGenerator(earth);
    const R = earth.radius;
    const rnd = mulberry32(23);
    const walk = (start: [number, number, number], heading: [number, number, number], steps: number, stepM: number) => {
      // March along the great circle through `start` toward `heading`, 1 m steps (gameplay metres).
      let worst = 0;
      let prev = g.height(start[0], start[1], start[2]);
      for (let k = 1; k <= steps; k++) {
        const t = (k * stepM) / R;
        const c = Math.cos(t);
        const s = Math.sin(t);
        const x = start[0] * c + heading[0] * s;
        const y = start[1] * c + heading[1] * s;
        const z = start[2] * c + heading[2] * s;
        const h = g.height(x, y, z);
        worst = Math.max(worst, Math.abs(h - prev));
        prev = h;
      }
      return worst;
    };
    const tangent = (d: [number, number, number], toward: [number, number, number]): [number, number, number] => {
      const k = toward[0] * d[0] + toward[1] * d[1] + toward[2] * d[2];
      const v = [toward[0] - k * d[0], toward[1] - k * d[1], toward[2] - k * d[2]];
      const l = Math.hypot(v[0], v[1], v[2]);
      return [v[0] / l, v[1] / l, v[2] / l];
    };
    // Random paths, plus paths crossing the date line (Fiji, Chukotka, Ross Ice Shelf) and both poles.
    let worst = 0;
    for (let i = 0; i < 40; i++) {
      const start = randomDir(rnd);
      worst = Math.max(worst, walk(start, tangent(start, randomDir(rnd)), 400, 1));
    }
    for (const [lat, lon] of [[-17, 179.9], [66, 179.9], [-80, 179.9], [89.999, 30], [-89.999, 30]]) {
      const d = dirOf(lat, lon);
      const east = tangent(d, dirOf(lat, lon > 0 ? -179.9 : 179.9));
      const toPole = tangent(d, dirOf(lat > 0 ? 90 : -90, 0));
      worst = Math.max(worst, walk(d, Math.abs(lat) > 89 ? toPole : east, 600, 1));
    }
    // Slopes up to ~70° give at most ~3 m per metre; anything larger is a step.
    expect(worst).toBeLessThan(3);
  });

  it('generates identical chunks regardless of job order and agrees across a cube-face edge', () => {
    const sites = computeSites(earth);
    const gen = new SurfaceGenerator(earth);
    gen.clearings = sites.clearings;
    const level = earth.maxLevel - 3;
    const M = gridResolution(earth.maxLevel);
    const d = [0, 0, 0];
    gridDir(0, 0, M / 2 + 777, M, d); // on the +X / +Z edge
    const fa = dirToFace(d[0] + 1e-9, d[1], d[2] - 1e-9);
    const fb = dirToFace(d[0] - 1e-9, d[1], d[2] + 1e-9);
    const ca = chunkAt(fa.face, fa.u, fa.v, level);
    const cb = chunkAt(fb.face, fb.u, fb.v, level);
    const A = generateChunk(earth, gen, fa.face, level, ca.x, ca.y, 1);
    generateChunk(earth, gen, 3, 4, 2, 9, 1); // unrelated work in between
    const fresh = new SurfaceGenerator(earth);
    fresh.clearings = sites.clearings;
    const A2 = generateChunk(earth, fresh, fa.face, level, ca.x, ca.y, 1);
    expect(Array.from(A2.positions)).toEqual(Array.from(A.positions));
    expect(Array.from(A2.attrs)).toEqual(Array.from(A.attrs));
    const B = generateChunk(earth, gen, fb.face, level, cb.x, cb.y, 1);
    // Border vertices of both chunks at the same world point coincide.
    const pts = (c: typeof A) => {
      const out: number[][] = [];
      for (let k = 0; k < 33 * 33; k++) out.push([c.center[0] + c.positions[k * 3], c.center[1] + c.positions[k * 3 + 1], c.center[2] + c.positions[k * 3 + 2]]);
      return out;
    };
    const pa = pts(A);
    const pb = pts(B);
    let shared = 0;
    for (const p of pa) {
      for (const q of pb) {
        if (Math.hypot(p[0] - q[0], p[1] - q[1], p[2] - q[2]) < 0.05) {
          shared++;
          break;
        }
      }
    }
    expect(shared).toBe(33);
  });

  it('keeps proxy roots and surface continuous over the Southern Alps (orbit to ground)', () => {
    const gen = new SurfaceGenerator(earth);
    gen.clearings = computeSites(earth).clearings;
    // Transect: Tasman Sea -> West Coast -> Aoraki / Mount Cook.
    const from = dirOf(-43.25, 169.75);
    const to = dirOf(-43.6, 170.14);
    const info = newSurfaceInfo();
    gen.info(from[0], from[1], from[2], info);
    expect(info.liquidLevel).toBe(sea);
    gen.info(to[0], to[1], to[2], info);
    expect(info.liquidLevel).toBeNull();
    expect(info.height).toBeGreaterThan(sea + 150);
    // The proxy is built from the level-0 roots; the terrain refines them. Every
    // level's vertex that lies on a coarser level's vertex has the same position,
    // and each level's mesh converges to the generator surface at the summit.
    const fc = dirToFace(to[0], to[1], to[2]);
    const R = earth.radius;
    const trueH = gen.height(to[0], to[1], to[2]);
    const errs: number[] = [];
    let parent: ReturnType<typeof generateChunk> | null = null;
    for (const level of [0, 1, 2, 4, 6, 8, earth.maxLevel]) {
      const c = chunkAt(fc.face, fc.u, fc.v, level);
      const ch = generateChunk(earth, gen, fc.face, level, c.x, c.y, 1);
      // Nearest vertex to the summit direction: its radial height vs the true surface there.
      let best = Infinity;
      let bestK = 0;
      for (let k = 0; k < 33 * 33; k++) {
        const x = ch.center[0] + ch.positions[k * 3];
        const y = ch.center[1] + ch.positions[k * 3 + 1];
        const z = ch.center[2] + ch.positions[k * 3 + 2];
        const l = Math.hypot(x, y, z);
        const dd = Math.hypot(x / l - to[0], y / l - to[1], z / l - to[2]);
        if (dd < best) { best = dd; bestK = k; }
      }
      const vx = ch.center[0] + ch.positions[bestK * 3];
      const vy = ch.center[1] + ch.positions[bestK * 3 + 1];
      const vz = ch.center[2] + ch.positions[bestK * 3 + 2];
      const vl = Math.hypot(vx, vy, vz);
      // Mesh vertices lie exactly on the generator surface (float32 positions, ~cm).
      expect(Math.abs(vl - (R + gen.height(vx / vl, vy / vl, vz / vl)))).toBeLessThan(0.05);
      errs.push(Math.abs(vl - R - trueH)); // height mismatch at the nearest vertex
      if (parent && level === 1) {
        // Level-1 vertices with even grid indices coincide with level-0 vertices.
        const ox = (c.x % 2) * 16;
        const oy = (c.y % 2) * 16;
        for (let j = 0; j <= 32; j += 2) {
          for (let i = 0; i <= 32; i += 2) {
            const k1 = j * 33 + i;
            const k0 = (oy + j / 2) * 33 + (ox + i / 2);
            for (let a = 0; a < 3; a++) {
              const p1 = ch.center[a] + ch.positions[k1 * 3 + a];
              const p0 = parent.center[a] + parent.positions[k0 * 3 + a];
              expect(Math.abs(p1 - p0)).toBeLessThan(0.05);
            }
          }
        }
      }
      parent = ch;
    }
    // The finest level resolves the summit to within a few metres.
    expect(errs[errs.length - 1]).toBeLessThan(5);
  });

  it('draws liquid surfaces only over water and the first dry row, never above dry ground', () => {
    const gen = new SurfaceGenerator(earth);
    gen.clearings = computeSites(earth).clearings;
    const info = newSurfaceInfo();
    const R = earth.radius;
    const check = (lat: number, lon: number, level: number) => {
      const d = dirOf(lat, lon);
      const fc = dirToFace(d[0], d[1], d[2]);
      const c = chunkAt(fc.face, fc.u, fc.v, level);
      const ch = generateChunk(earth, gen, fc.face, level, c.x, c.y, 1);
      let wet = 0;
      let drawn = 0;
      for (let k = 0; k < 33 * 33; k++) {
        const x = ch.center[0] + ch.positions[k * 3], y = ch.center[1] + ch.positions[k * 3 + 1], z = ch.center[2] + ch.positions[k * 3 + 2];
        const l = Math.hypot(x, y, z);
        gen.info(x / l, y / l, z / l, info);
        if (info.liquidLevel != null) wet++;
      }
      if (!ch.water) return { wet, drawn, water: false };
      const used = new Set(ch.water.index);
      for (const k of used) {
        drawn++;
        const wx = ch.center[0] + ch.water.positions[k * 3], wy = ch.center[1] + ch.water.positions[k * 3 + 1], wz = ch.center[2] + ch.water.positions[k * 3 + 2];
        const tx = ch.center[0] + ch.positions[k * 3], ty = ch.center[1] + ch.positions[k * 3 + 1], tz = ch.center[2] + ch.positions[k * 3 + 2];
        const wl = Math.hypot(wx, wy, wz) - R;
        const tl = Math.hypot(tx, ty, tz) - R;
        // Wet vertices: water above the bed; borrowed (dry) vertices: terrain above the water, so the shore hides them.
        if (ch.water.depth[k] > 0) expect(wl).toBeGreaterThan(tl - 0.05);
        else expect(tl).toBeGreaterThan(wl - 0.05);
      }
      return { wet, drawn, water: true };
    };
    const coast = check(-43.35, 170.0, 9); // West Coast shoreline
    expect(coast.water).toBe(true);
    expect(coast.wet).toBeGreaterThan(0);
    expect(coast.drawn).toBeGreaterThanOrEqual(coast.wet);
    const open = check(-40, -140, 6); // open Pacific
    expect(open.water).toBe(true);
    expect(open.drawn).toBe(33 * 33);
    const desert = check(23, 10, 9); // Sahara: no liquid anywhere
    expect(desert.water).toBe(false);
    // The Quiet System has no liquids.
    const ilex = BODIES.ilex;
    const ig = new SurfaceGenerator(ilex);
    expect(generateChunk(ilex, ig, 2, 5, 11, 7, 1).water).toBeNull();
  });

  it('keeps land near high lakes at or above the lake and close to the data (no trenches or craters)', () => {
    const g = new SurfaceGenerator(earth);
    const info = newSurfaceInfo();
    const ll = { lat: 0, lon: 0 };
    const cs = { v: 0, dLon: 0, dLat: 0 };
    const f = earth.frame;
    let checked = 0;
    // Rings around Titicaca, Nam Co, Qinghai and Sevan, 1-60 km (real) from their centres.
    for (const [lat0, lon0] of [[-15.8, -69.4], [30.7, 90.6], [36.9, 100.2], [40.35, 45.3]]) {
      for (let r = 0.05; r <= 0.6; r += 0.05) {
        for (let k = 0; k < 24; k++) {
          const t = (k / 24) * 2 * Math.PI;
          const d = dirOf(lat0 + r * Math.sin(t), lon0 + (r * Math.cos(t)) / Math.cos((lat0 * Math.PI) / 180));
          g.info(d[0], d[1], d[2], info);
          latLonOf(d[0], d[1], d[2], f.north, f.meridian, f.east, ll);
          const shore = sampleCubic(E.coast, ll.lat, ll.lon, cs).v;
          if (shore <= 0) continue;
          const W = sampleBilinear(E.water, ll.lat, ll.lon);
          const real = (info.height - sea) * 5; // gameplay relief is real / 5
          const e = sampleCubic(E.elevation, ll.lat, ll.lon, cs).v;
          if (shore < 3) expect(real).toBeGreaterThanOrEqual(W * 0.98);
          else expect(real).toBeGreaterThan(e - 700); // infill reaches at most ~600 m below the data
          checked++;
        }
      }
    }
    expect(checked).toBeGreaterThan(300);
    // Anywhere on land at least 3 km from a shore, the surface stays near the data.
    const rnd = mulberry32(41);
    let land = 0;
    for (let i = 0; i < 6000; i++) {
      const d = randomDir(rnd);
      latLonOf(d[0], d[1], d[2], f.north, f.meridian, f.east, ll);
      if (sampleCubic(E.coast, ll.lat, ll.lon, cs).v < 3) continue;
      g.info(d[0], d[1], d[2], info);
      const e = sampleCubic(E.elevation, ll.lat, ll.lon, cs).v;
      expect((info.height - sea) * 5).toBeGreaterThan(e - 700);
      land++;
    }
    expect(land).toBeGreaterThan(1000);
  });

  it('adds detail below the data resolution only: box means barely depend on the seed', () => {
    const other: BodyDef = { ...earth, seed: (earth.seed ^ 0x5bd1e995) >>> 0 };
    const a = new SurfaceGenerator(earth);
    const b = new SurfaceGenerator(other);
    let worst = 0;
    // 0.5° boxes (3 x 3 elevation cells) in the Himalaya, Andes, Alps and on the Antarctic plateau.
    for (let i = 0; i < 8; i++) {
      for (const [la, lo] of [[28 + i * 0.5, 84 + i * 1.3], [-15 - i * 2, -70 + i * 0.2], [46 + i * 0.2, 7 + i * 0.5], [-80 + i * 2, 40 + i * 10]]) {
        let sa = 0;
        let sb = 0;
        for (let p = 0; p < 15; p++) {
          for (let q = 0; q < 15; q++) {
            const d = dirOf(la + (p * 0.5) / 14, lo + (q * 0.5) / 14);
            sa += a.height(d[0], d[1], d[2]);
            sb += b.height(d[0], d[1], d[2]);
          }
        }
        worst = Math.max(worst, (Math.abs(sa - sb) / 225) * 5);
      }
    }
    expect(worst).toBeLessThan(40); // real metres (measured 16 m)
  });

  it('exposes latitude/longitude helpers, the subsolar point and the data elevation', () => {
    for (const [lat, lon] of [[27.99, 86.93], [-43.6, 170.14], [0, -179.5], [-89.9, 12]]) {
      const d = geoToDir(earth, lat, lon);
      const g = dirToGeo(earth, d[0] * 3, d[1] * 3, d[2] * 3);
      expect(g.lat).toBeCloseTo(lat, 9);
      expect(g.lon).toBeCloseTo(lon, 9);
    }
    const s = subsolarPoint(earth);
    expect(s.lat).toBeCloseTo(-23.02, 1);
    expect(s.lon).toBeCloseTo(-178.87, 1);
    expect(earthElevationM(27.99, 86.93)!).toBeGreaterThan(5000);
    expect(earthElevationM(11.35, 142.2)!).toBeLessThan(-8000);
    // The infill bound holds over random points.
    const g = new SurfaceGenerator(earth);
    const info = newSurfaceInfo();
    const rnd = mulberry32(77);
    const ll = { lat: 0, lon: 0 };
    const cs = { v: 0, dLon: 0, dLat: 0 };
    for (let i = 0; i < 3000; i++) {
      const d = randomDir(rnd);
      latLonOf(d[0], d[1], d[2], earth.frame.north, earth.frame.meridian, earth.frame.east, ll);
      if (Math.abs(sampleCubic(E.coast, ll.lat, ll.lon, cs).v) < 30) continue; // shore shaping applies there
      g.info(d[0], d[1], d[2], info);
      if (info.liquidLevel != null) continue;
      const real = (info.height - sea) * 5;
      expect(Math.abs(real - sampleCubic(E.elevation, ll.lat, ll.lon, cs).v)).toBeLessThan(EARTH_INFILL_MAX_M + 1);
    }
  });
});
