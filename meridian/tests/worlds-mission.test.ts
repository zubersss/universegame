// LEAD IFACE F: mission objects per system. Quiet System: relay mast and
// samples as before. Sol: First Light route beacons (kind 'route', lit once
// reached) and scan targets (kind 'scan', labelled landmarks).
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { beforeAll, describe, expect, it } from 'vitest';
import { initPhysics, Physics } from '../src/physics/Physics';
import { BODIES } from '../src/world/bodies';
import { EARTH_META, installEarthData, loadEarthData, type LayerName } from '../src/world/earthData';
import { MissionObjects, sampleName } from '../src/world/MissionObjects';
import { computeSites } from '../src/world/sites';
import { getSurface, newSurfaceInfo } from '../src/world/surface';
import { FIRST_LIGHT, SURVEY_BODIES } from '../src/world/survey';
import { Vector3 } from 'three';

beforeAll(async () => {
  await initPhysics();
  const dir = fileURLToPath(new URL('../src/data/earth/', import.meta.url));
  const layers = EARTH_META.layers as Record<LayerName, { file: string }>;
  installEarthData(await loadEarthData(async (name) => readFileSync(dir + layers[name].file)));
});

function build(id: string) {
  const def = BODIES[id];
  const sites = computeSites(def);
  const gen = getSurface(def, sites.clearings);
  const physics = new Physics();
  return { def, sites, gen, physics, mo: new MissionObjects(def, sites, gen, physics, 4) };
}

type MastView = { id: string; active: boolean };
const mastsOf = (mo: MissionObjects) => (mo as unknown as { masts: MastView[] }).masts;

describe('mission objects (F)', () => {
  it('keeps the Quiet System relay mast and three samples on the ground', () => {
    for (const id of ['ilex', 'vesper', 'cairn']) {
      const { sites, gen, physics, mo } = build(id);
      expect(mo.targets.map((t) => t.kind)).toEqual(['relay', 'sample', 'sample', 'sample']);
      expect(mo.targets[0].id).toBe(sites.relay.id);
      const R = BODIES[id].radius;
      for (const t of mo.targets) {
        const ground = R + gen.height(t.up.x, t.up.y, t.up.z);
        const above = t.pos.length() - ground;
        expect(above, t.id).toBeGreaterThan(0);
        expect(above, t.id).toBeLessThan(4);
        expect(t.label).toBeUndefined();
      }
      mo.installCollider(new Vector3());
      expect(mo.hasCollider).toBe(true);
      mo.sync(() => false, true);
      expect(mastsOf(mo).map((m) => m.active)).toEqual([true]);
      mo.removeCollider();
      expect(mo.hasCollider).toBe(false);
      expect(physics.bodyCount).toBe(0);
      mo.dispose();
    }
  });

  it('builds three lit-on-arrival route beacons and three labelled scan targets on each survey body', () => {
    for (const id of SURVEY_BODIES) {
      const { def, gen, physics, mo } = build(id);
      const spec = FIRST_LIGHT[id];
      const routes = mo.targets.filter((t) => t.kind === 'route');
      const scans = mo.targets.filter((t) => t.kind === 'scan');
      expect(mo.targets.length).toBe(6);
      expect(routes.map((t) => t.id)).toEqual([`${id}:route:0`, `${id}:route:1`, `${id}:route:2`]);
      expect(scans.map((t) => t.id)).toEqual([`${id}:poi:0`, `${id}:poi:1`, `${id}:poi:2`]);
      routes.forEach((t, i) => {
        expect(t.label).toBe(spec.route[i].label);
        expect(t.arrive).toBe(spec.route[i].radius);
      });
      scans.forEach((t, i) => {
        expect(t.label).toBe(spec.scans[i].label);
        expect(t.note).toBe(spec.scans[i].note);
        expect(t.tag).toBe('estimated');
      });
      // Every target stands on the ground, or on the water where the site is wet.
      const info = newSurfaceInfo();
      for (const t of mo.targets) {
        gen.info(t.up.x, t.up.y, t.up.z, info);
        const top = def.radius + Math.max(info.height, info.liquidLevel ?? -Infinity);
        const above = t.pos.length() - top;
        expect(above, `${t.id} ${t.label}`).toBeGreaterThan(0);
        expect(above, `${t.id} ${t.label}`).toBeLessThan(4);
      }
      // One collider per beacon; lamps follow the reached set.
      mo.installCollider(new Vector3());
      expect(physics.bodyCount).toBe(3);
      mo.sync(() => false, false, (rid) => rid === `${id}:route:1`);
      expect(mastsOf(mo).map((m) => m.active)).toEqual([false, true, false]);
      mo.sync(() => false, false);
      expect(mastsOf(mo).map((m) => m.active)).toEqual([false, false, false]);
      mo.dispose();
      expect(physics.bodyCount).toBe(0);
    }
  });

  it('gives other Sol bodies no mission objects and a safe sample name', () => {
    const { mo } = build('mercury');
    expect(mo.targets).toEqual([]);
    expect(mo.hasCollider).toBe(false);
    expect(sampleName('mercury')).toBe('Sample');
    expect(sampleName('ilex')).toBe('Chalk nodule');
  });
});
