// W8 (PLAYER DEFECT): collision streaming along a superspeed run. Redline at
// 110 m/s over Mars from the landing site on five headings, with the demand
// loop Game uses (computeWanted on the walker's velocity, chunk results, then
// TerrainCollision.update every step). The corridor ahead (speed x 2 s +
// braking distance + 50 m, as wide as the walker) must load front to back with
// no holes, and tiles must not be evicted and re-requested while still needed.
import { beforeAll, describe, expect, it } from 'vitest';
import { Vector3 } from 'three';
import { initPhysics, Physics } from '../src/physics/Physics';
import { BODIES } from '../src/world/bodies';
import { computeSites, tangentBasis } from '../src/world/sites';
import { getSurface } from '../src/world/surface';
import { ChunkStore } from '../src/terrain/ChunkStore';
import { TerrainCollision } from '../src/terrain/TerrainCollision';
import { FakeBackend } from './fakeBackend';

beforeAll(async () => {
  await initPhysics();
});

const SPEED = 110; // charter K: Redline top speed
const DECEL = 56; // what Game passes (FLIGHT.brakeAtmo * 0.8)
const DT = 1 / 60;
const WALKER = 0.6; // capsule radius plus a margin [m]

describe('collision corridor at superspeed (W8)', () => {
  it('loads the corridor ahead without holes and never evicts tiles still in use', () => {
    const def = BODIES.mars;
    const sites = computeSites(def);
    const gen = getSurface(def, sites.clearings);
    const R = def.radius;
    const ahead = SPEED * 2 + (SPEED * SPEED) / (2 * DECEL) + 50; // 378 m
    let holeSteps = 0;
    let worstHole = '';
    let flicker = 0;
    let steps = 0;
    for (let k = 0; k < 5; k++) {
      const physics = new Physics();
      const backend = new FakeBackend();
      const store = new ChunkStore(backend, def.id);
      store.maxInFlight = 16;
      const col = new TerrainCollision(physics, def, store);
      const start = sites.landing.dir;
      const [t1, t2] = tangentBasis(start);
      const a = (k / 5) * Math.PI * 2 + 0.3;
      // Great circle through the landing site along heading a.
      const p0 = new Vector3(...start);
      const tdir = new Vector3(...t1).multiplyScalar(Math.cos(a)).addScaledVector(new Vector3(...t2), Math.sin(a));
      const at = (s: number) => {
        const th = s / R;
        const d = p0.clone().multiplyScalar(Math.cos(th)).addScaledVector(tdir, Math.sin(th));
        return { d, t: p0.clone().multiplyScalar(-Math.sin(th)).addScaledVector(tdir, Math.cos(th)) };
      };
      const removedAt = new Map<string, number>();
      let prev = new Set<string>();
      for (let i = 0; i < 12 / DT; i++) {
        const s = SPEED * i * DT;
        const { d, t } = at(s);
        const focus = d.clone().multiplyScalar(R + gen.height(d.x, d.y, d.z) + 1);
        const vel = t.multiplyScalar(i < 30 ? (SPEED * i) / 30 : SPEED); // half a second to reach top speed
        store.setDemand(col.computeWanted(focus, vel, 0, DECEL));
        backend.tick();
        col.update(new Vector3(), DT);
        // Flicker: a tile removed and installed again within a second.
        const now = col.installedKeys();
        for (const key of prev) if (!now.has(key)) removedAt.set(key, i);
        for (const key of now) {
          const r = removedAt.get(key);
          if (r !== undefined && !prev.has(key) && i - r < 60) flicker++;
        }
        prev = now;
        if (i < 90) continue; // warm-up: the first tiles are still being generated
        steps++;
        // Holes: walk the corridor (centre and both sides of the walker) at 1 m steps.
        let gap = -1;
        const marks: string[] = [];
        for (let m = 0; m <= ahead; m += 1) {
          const q = at(s + m).d;
          const side = new Vector3().crossVectors(q, at(s + m).t).normalize();
          const ok = [-WALKER, 0, WALKER].every((o) => {
            const p = q.clone().addScaledVector(side, o / R).normalize();
            return col.has(col.keyForDir(p.x, p.y, p.z));
          });
          if (m % 25 === 0) marks.push(ok ? '#' : '.');
          if (!ok && gap < 0) gap = m;
          else if (ok && gap >= 0) {
            holeSteps++;
            if (!worstHole) worstHole = `heading ${k} t=${(i * DT).toFixed(2)}s hole at ${gap} m before ${m} m: ${marks.join('')}`;
            break;
          }
        }
      }
    }
    expect(steps).toBeGreaterThan(5 * 600);
    expect(holeSteps, worstHole).toBe(0);
    expect(flicker).toBe(0);
  });
});
