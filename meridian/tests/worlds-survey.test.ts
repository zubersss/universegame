// LEAD IFACE E: landing sites, First Light routes and scan targets for Sol.
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { beforeAll, describe, expect, it } from 'vitest';
import { BODIES, SYSTEM_BODY_IDS, sunDirFor } from '../src/world/bodies';
import { installEarthData, loadEarthData } from '../src/world/earthData';
import { dirToGeo } from '../src/world/geo';
import { computeSites } from '../src/world/sites';
import { getSurface, newSurfaceInfo } from '../src/world/surface';
import { FIRST_LIGHT, SURVEY_BODIES } from '../src/world/survey';

beforeAll(async () => {
  const dir = fileURLToPath(new URL('../src/data/earth/', import.meta.url));
  installEarthData(await loadEarthData(async (_name, _url, file) => readFileSync(dir + file)));
});

const dot = (a: readonly number[], b: readonly number[]) => a[0] * b[0] + a[1] * b[1] + a[2] * b[2];

describe('First Light survey sites', () => {
  it('refuses a landing site on the Sun', () => {
    expect(() => computeSites(BODIES.sun)).toThrow(/no surface/);
  });

  it('keeps the Quiet System survey (relay pad, samples) and gives it no route', () => {
    for (const id of SYSTEM_BODY_IDS.quiet) {
      const s = computeSites(BODIES[id]);
      expect(s.route).toEqual([]);
      expect(s.scans).toEqual([]);
      expect(s.samples.length).toBe(3);
      expect(s.clearings.length).toBe(2);
    }
  });

  it('places three route waypoints and three scan targets on Earth, the Moon and Mars, in daylight', () => {
    expect(SURVEY_BODIES).toEqual(['earth', 'moon', 'mars']);
    for (const id of SURVEY_BODIES) {
      const def = BODIES[id];
      const s = computeSites(def);
      const spec = FIRST_LIGHT[id];
      expect(s.route.map((r) => r.id)).toEqual([`${id}:route:0`, `${id}:route:1`, `${id}:route:2`]);
      expect(s.scans.map((r) => r.id)).toEqual([`${id}:poi:0`, `${id}:poi:1`, `${id}:poi:2`]);
      const sun = sunDirFor(def);
      for (const p of [...s.route, ...s.scans]) {
        expect(Math.hypot(...p.dir)).toBeCloseTo(1, 12);
        expect(dot(p.dir, sun), `${p.id} ${p.label} in daylight`).toBeGreaterThan(0.2);
      }
      s.route.forEach((r, i) => {
        const g = dirToGeo(def, ...r.dir);
        expect(g.lat).toBeCloseTo(spec.route[i].lat, 6);
        const lon = ((((spec.route[i].lon + 180) % 360) + 360) % 360) - 180; // same meridian in (-180, 180]
        expect(g.lon).toBeCloseTo(lon, 6);
        expect(r.radius).toBeGreaterThan(0);
      });
      for (const t of s.scans) expect(['measured', 'estimated', 'fictional']).toContain(t.tag);
      // Landing: near the route start (real km), sunlit, dry, one clearing, no samples.
      const l = s.landing.dir;
      const realR = def.real!.radiusKm;
      const near = spec.landingNear;
      const g = dirToGeo(def, ...l);
      const dLat = ((g.lat - near.lat) * Math.PI) / 180;
      const dLon = (((((g.lon - near.lon + 540) % 360) + 360) % 360 - 180) * Math.PI) / 180;
      const km = realR * Math.sqrt(dLat * dLat + (Math.cos((near.lat * Math.PI) / 180) * dLon) ** 2);
      expect(km).toBeLessThan(near.maxKm + 60); // the local refinement may move it up to ~1.4 km of gameplay surface
      expect(dot(l, sun)).toBeGreaterThan(0.25);
      expect(s.samples).toEqual([]);
      expect(s.clearings.length).toBe(1);
      const info = getSurface(def, s.clearings).info(l[0], l[1], l[2], newSurfaceInfo());
      expect(info.liquidLevel ?? null).toBeNull();
      if (def.seaLevel != null) expect(info.height).toBeGreaterThan(def.seaLevel);
    }
  });

  it('gives other Sol bodies a landing site but no First Light content', () => {
    for (const id of ['mercury', 'venus']) {
      const s = computeSites(BODIES[id]);
      expect(s.route).toEqual([]);
      expect(s.scans).toEqual([]);
      expect(dot(s.landing.dir, sunDirFor(BODIES[id]))).toBeGreaterThan(0.3);
    }
  });
});
