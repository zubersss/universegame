// W6: Mars and Moon surfaces with large real features (plus the other Sol
// procedural bodies): determinism, bounds, features where they belong, the
// First Light route terrain (Ma'adim Vallis, the Ariadaeus crevasse field).
import { describe, expect, it } from 'vitest';
import { BODIES, type BodyDef } from '../src/world/bodies';
import { geoToDir } from '../src/world/geo';
import { SurfaceGenerator, newSurfaceInfo } from '../src/world/surface';
import { computeSites } from '../src/world/sites';
import { mulberry32 } from '../src/core/rng';
import { generateChunk, GRID_VERTS, levelSpacing } from '../src/terrain/chunkGen';
import { dirToFace, chunkAt } from '../src/world/cube';

const mars = BODIES.mars;
const moon = BODIES.moon;

function at(def: BodyDef, g: SurfaceGenerator, lat: number, lon: number) {
  const d = geoToDir(def, lat, lon);
  return { ...g.info(d[0], d[1], d[2], newSurfaceInfo()) };
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

describe('Sol procedural surfaces (W6)', () => {
  it('are deterministic, bounded and continuous for every landable Sol body', () => {
    for (const id of ['mercury', 'venus', 'moon', 'mars', 'europa', 'titan']) {
      const def = BODIES[id];
      const a = new SurfaceGenerator(def);
      const b = new SurfaceGenerator(def);
      const ia = newSurfaceInfo();
      const ib = newSurfaceInfo();
      const rnd = mulberry32(9);
      for (let i = 0; i < 1500; i++) {
        const d = randomDir(rnd);
        a.info(d[0], d[1], d[2], ia);
        b.info(d[0], d[1], d[2], ib);
        expect(ia).toEqual(ib);
        expect(ia.height, id).toBeGreaterThan(0); // above the datum before clamping (no flattened floors)
        expect(ia.height, id).toBeLessThan(def.maxHeight);
        expect(ia.liquidLevel).toBeNull();
        for (const k of ['biome', 'variation', 'special', 'rockiness'] as const) {
          expect(ia[k]).toBeGreaterThanOrEqual(0);
          expect(ia[k]).toBeLessThanOrEqual(1);
        }
      }
    }
  });

  it('puts the large Martian features where they belong', () => {
    const g = new SurfaceGenerator(mars);
    const h = (lat: number, lon: number) => at(mars, g, lat, lon).height;
    // Olympus Mons towers ~4 km (gameplay; 21 km real) over the plains to its west.
    expect(h(18.65, 226.2) - h(18.65, 205)).toBeGreaterThan(3000);
    // Hellas is deep: kilometres below the surrounding highlands.
    expect(h(-20, 70.5) - h(-42.4, 70.5)).toBeGreaterThan(900);
    // Northern lowlands sit below the southern highlands.
    expect(h(-30, 20) - h(60, 180)).toBeGreaterThan(500);
    // Ma'adim Vallis is a canyon (the Redline route runs along its floor); Gusev is a crater.
    expect(h(-23.6, 182.0) - h(-23.5, 179.0)).toBeGreaterThan(250);
    expect(h(-14.57, 175.47 + 1.6) - h(-14.57, 175.47)).toBeGreaterThan(150);
    // Polar caps.
    expect(at(mars, g, 85, 0).special).toBeGreaterThan(0.9);
    expect(at(mars, g, 0, 0).special).toBe(0);
    // Classical dark albedo regions over bright dusty ground.
    expect(at(mars, g, 9, 69).biome).toBeGreaterThan(0.75); // Syrtis Major
    expect(at(mars, g, 46, 330).biome).toBeGreaterThan(0.7); // Mare Acidalium
    expect(at(mars, g, 20, 15).biome).toBeLessThan(0.4); // Arabia Terra
    expect(at(mars, g, 0, 255).biome).toBeLessThan(0.4); // Tharsis
  });

  it('fades procedural variation noise on levels too coarse to resolve it', () => {
    for (const def of [mars, moon]) {
      const g = new SurfaceGenerator(def);
      const d = geoToDir(def, 10, 20);
      const f = dirToFace(d[0], d[1], d[2]);
      const spread = (level: number) => {
        const c = chunkAt(f.face, f.u, f.v, level);
        const ch = generateChunk(def, g, f.face, level, c.x, c.y, 1);
        let lo = 255;
        let hi = 0;
        for (let i = 0; i < GRID_VERTS; i++) {
          lo = Math.min(lo, ch.attrs[i * 4 + 2]);
          hi = Math.max(hi, ch.attrs[i * 4 + 2]);
        }
        return hi - lo;
      };
      expect(spread(0), def.id).toBe(0); // neutral: no aliased blotches on the proxy
      // Full noise once vertices resolve it (spacing <= 700 m; the chunk then spans several wavelengths).
      let level = 0;
      while (levelSpacing(def, level) > 700) level++;
      expect(spread(level), def.id).toBeGreaterThan(80);
    }
  });

  it('puts the lunar maria, craters and the Ariadaeus crevasses where they belong', () => {
    const g = new SurfaceGenerator(moon);
    expect(at(moon, g, 8.5, 31.4).biome).toBeGreaterThan(0.9); // Mare Tranquillitatis: dark
    expect(at(moon, g, -30, 10).biome).toBeLessThan(0.1); // southern highlands: bright
    expect(at(moon, g, -38, -11.2).height - at(moon, g, -43.3, -11.2).height).toBeGreaterThan(500); // Tycho's floor
    // Walk across the crevasse field along the route: cracks about 55 m apart (gameplay), each deep.
    const route = computeSites(moon).route;
    const a = route[0].dir;
    const b = route[2].dir;
    const steps = 4000;
    const hs: number[] = [];
    for (let i = 0; i <= steps; i++) {
      const t = i / steps;
      const x = a[0] + (b[0] - a[0]) * t, y = a[1] + (b[1] - a[1]) * t, z = a[2] + (b[2] - a[2]) * t;
      const l = Math.hypot(x, y, z);
      hs.push(g.height(x / l, y / l, z / l));
    }
    // A crack: more than 25 m below the highest ground within ~25 m either side.
    const win = Math.round((25 / (Math.acos(a[0] * b[0] + a[1] * b[1] + a[2] * b[2]) * moon.radius)) * steps);
    let inCrack = false;
    let cracks = 0;
    let deepest = 0;
    for (let i = win; i <= steps - win; i++) {
      let top = -Infinity;
      for (let j = i - win; j <= i + win; j++) top = Math.max(top, hs[j]);
      const drop = top - hs[i];
      deepest = Math.max(deepest, drop);
      const crack = drop > 25;
      if (crack && !inCrack) cracks++;
      inCrack = crack;
    }
    expect(cracks).toBeGreaterThanOrEqual(5);
    expect(cracks).toBeLessThan(30);
    expect(deepest).toBeGreaterThan(50);
  });

  it('keeps Mars and Moon surfaces continuous away from the crevasse walls', () => {
    for (const def of [mars, moon]) {
      const g = new SurfaceGenerator(def);
      const rnd = mulberry32(31);
      let worst = 0;
      for (let k = 0; k < 30; k++) {
        const s = randomDir(rnd);
        const t0 = randomDir(rnd);
        const dd = t0[0] * s[0] + t0[1] * s[1] + t0[2] * s[2];
        const tv = [t0[0] - dd * s[0], t0[1] - dd * s[1], t0[2] - dd * s[2]];
        const tl = Math.hypot(tv[0], tv[1], tv[2]);
        let prev = g.height(s[0], s[1], s[2]);
        for (let i = 1; i <= 300; i++) {
          const th = i / def.radius;
          const c = Math.cos(th);
          const sn = Math.sin(th);
          const x = s[0] * c + (tv[0] / tl) * sn, y = s[1] * c + (tv[1] / tl) * sn, z = s[2] * c + (tv[2] / tl) * sn;
          const hh = g.height(x, y, z);
          worst = Math.max(worst, Math.abs(hh - prev));
          prev = hh;
        }
      }
      expect(worst, def.id).toBeLessThan(5); // 1 m steps; canyon and crater walls stay below ~80 degrees
    }
  });
});
