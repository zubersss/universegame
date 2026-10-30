// Scenery props on the First Light bodies: Earth trees and rocks from the
// land-cover data (on land only, below the snow), lunar and Martian boulders;
// one scannable rock type per airless survey body; deterministic placement.
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { beforeAll, describe, expect, it } from 'vitest';
import { Vector3 } from 'three';
import { initPhysics, Physics } from '../src/physics/Physics';
import { BODIES } from '../src/world/bodies';
import { installEarthData, loadEarthData } from '../src/world/earthData';
import { geoToDir } from '../src/world/geo';
import { computeSites } from '../src/world/sites';
import { getSurface, newSurfaceInfo, SurfaceGenerator } from '../src/world/surface';
import { SURVEY_BODIES } from '../src/world/survey';
import { PropSystem } from '../src/props/PropSystem';
import { speciesFor } from '../src/props/species';

beforeAll(async () => {
  await initPhysics();
  const dir = fileURLToPath(new URL('../src/data/earth/', import.meta.url));
  installEarthData(await loadEarthData(async (_name, _url, file) => readFileSync(dir + file)));
});

describe('Sol scenery props', () => {
  it('gives every survey body props with ids of the saved-species shape', () => {
    for (const id of SURVEY_BODIES) {
      const sp = speciesFor(id);
      expect(sp.length, id).toBeGreaterThan(0);
      for (const s of sp) expect(s.id).toMatch(new RegExp(`^${id}-[a-z]+$`));
    }
    expect(speciesFor('moon').filter((s) => s.scannable).map((s) => s.id)).toEqual(['moon-boulder']);
    expect(speciesFor('mars').filter((s) => s.scannable).map((s) => s.id)).toEqual(['mars-basalt']);
    expect(speciesFor('earth').filter((s) => s.scannable)).toEqual([]);
  });

  it('grows Earth forests where the land cover is forest, never on water, snow or desert', () => {
    const earth = BODIES.earth;
    const g = new SurfaceGenerator(earth);
    const info = newSurfaceInfo();
    const trees = speciesFor('earth').filter((s) => s.id === 'earth-conifer' || s.id === 'earth-broadleaf');
    const density = (lat: number, lon: number) => {
      const d = geoToDir(earth, lat, lon);
      g.info(d[0], d[1], d[2], info);
      return Math.max(...trees.map((s) => s.density(info, 0.05)));
    };
    expect(density(-42.85, 171.15)).toBeGreaterThan(0.3); // West Coast rainforest
    expect(density(60, 100)).toBeGreaterThan(0.3); // Siberian taiga
    expect(density(23, 10)).toBe(0); // Sahara
    expect(density(-43.595, 170.142)).toBe(0); // Aoraki's snowy summit
    for (const s of speciesFor('earth')) {
      const d = geoToDir(earth, -42.6, 170.5); // Tasman Sea
      g.info(d[0], d[1], d[2], info);
      expect(info.liquidLevel).not.toBeNull();
      expect(s.density(info, 0), s.id).toBe(0);
    }
  });

  it('places the same props for the same cells, on the ground, on the Moon and Mars', () => {
    for (const id of ['moon', 'mars']) {
      const def = BODIES[id];
      const sites = computeSites(def);
      const gen = getSurface(def, sites.clearings);
      const make = () => {
        const p = new PropSystem(def, gen, sites, new Physics(), 4);
        const at = new Vector3(...sites.landing.dir).multiplyScalar(def.radius + gen.height(...sites.landing.dir) + 2);
        for (let i = 0; i < 400; i++) p.update(0.016, at, at, new Vector3(), true);
        return p;
      };
      const a = make();
      const b = make();
      // The landing site on the ground (the datum lies kilometres below on the Moon and Mars).
      const site = new Vector3(...sites.landing.dir).multiplyScalar(def.radius + gen.height(...sites.landing.dir));
      const near = (p: PropSystem) => p.nearby(site, 400).map((x) => `${x.id}@${x.p.toArray().map((v) => v.toFixed(3)).join(',')}`).sort();
      const na = near(a);
      expect(na.length, id).toBeGreaterThan(5);
      expect(near(b)).toEqual(na);
      for (const inst of a.nearby(site, 400)) {
        const u = inst.p.clone().normalize();
        const ground = def.radius + gen.height(u.x, u.y, u.z);
        // Base sunk into the ground by its sink fraction, never floating.
        expect(inst.p.length() - ground, inst.id).toBeLessThanOrEqual(0.01);
        expect(inst.p.length() - ground, inst.id).toBeGreaterThan(-inst.h * inst.species.sink - 0.01);
      }
    }
  });
});
