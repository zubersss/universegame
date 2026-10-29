import { beforeAll, describe, expect, it } from 'vitest';
import { Vector3 } from 'three';
import { initPhysics, Physics, GROUPS } from '../src/physics/Physics';
import { ShipSim } from '../src/ship/Ship';
import { BODIES } from '../src/world/bodies';
import { computeSites } from '../src/world/sites';
import { getSurface } from '../src/world/surface';
import { FloatingOrigin } from '../src/core/origin';
import { ChunkStore } from '../src/terrain/ChunkStore';
import { TerrainCollision } from '../src/terrain/TerrainCollision';
import { FlightEnvProvider } from '../src/world/FlightEnvProvider';
import { NO_CONTROLS, type FlightOutput } from '../src/ship/FlightModel';
import { SIM_DT } from '../src/game/config';
import { quatFromForwardUp } from '../src/core/mathx';
import { FakeBackend } from './fakeBackend';

beforeAll(async () => {
  await initPhysics();
});

describe('floating origin rebasing', () => {
  it('preserves system positions, velocities, camera and immediate collision queries', () => {
    const def = BODIES.ilex;
    const sites = computeSites(def);
    const gen = getSurface(def, sites.clearings);
    const physics = new Physics();
    const fo = new FloatingOrigin();
    const n = new Vector3(...sites.landing.dir);
    const start = new Vector3(...def.center).addScaledVector(n, def.radius + gen.height(n.x, n.y, n.z) + 30);
    FloatingOrigin.rounded(start, fo.origin);
    const centerLocal = new Vector3(...def.center).sub(fo.origin);
    const fwd = new Vector3(0, 1, 0).cross(n).normalize();
    const ship = new ShipSim(physics, start.clone().sub(fo.origin), quatFromForwardUp(fwd, n));
    const backend = new FakeBackend();
    const store = new ChunkStore(backend, def.id);
    store.maxInFlight = 8;
    const col = new TerrainCollision(physics, def, store);
    const env = new FlightEnvProvider(def, centerLocal, fo.origin, (d) => gen.height(d.x, d.y, d.z));
    const out: FlightOutput = { force: new Vector3(), angvel: new Vector3() };
    const camera = new Vector3(); // stand-in for the camera's local position
    const sys = new Vector3();
    let rebases = 0;
    let maxPosErr = 0;
    let maxHitErr = 0;

    const radialHit = (): Vector3 | null => {
      const up = ship.currPos.clone().sub(centerLocal).normalize();
      const o = ship.currPos.clone().addScaledVector(up, 5);
      const h = physics.castRay(o.x, o.y, o.z, -up.x, -up.y, -up.z, 400, GROUPS.queryTerrain, ship.body);
      return h ? o.addScaledVector(up, -h.toi).add(fo.origin) : null; // system coordinates
    };

    for (let step = 0; step < 60 * 70; step++) {
      if (step % 6 === 0) {
        const fp = ship.currPos.clone().sub(centerLocal);
        store.setDemand(col.computeWanted(fp, ship.vel, env.update(ship.currPos).clearance, 50));
      }
      for (let k = 0; k < 4; k++) backend.tick();
      col.update(centerLocal);
      ship.beginStep();
      const e = env.update(ship.currPos);
      e.terrainSpeedLimit = col.speedLimit;
      // Terrain-following pilot: hold ~30 m clearance with the vertical control.
      const vertical = Math.max(-1, Math.min(1, (30 - e.clearance) / 15));
      ship.flight.step(SIM_DT, { pos: ship.currPos, vel: ship.vel, quat: ship.currQuat, angvel: ship.angvel }, { ...NO_CONTROLS, throttleAxis: 1, vertical }, e, out);
      ship.applyControl(out.force, out.angvel);
      physics.step();
      ship.syncFromBody();
      camera.copy(ship.currPos).add(new Vector3(0, 5, 14));

      if (fo.needsRebase(ship.currPos)) {
        const shipSysBefore = fo.toSystem(ship.currPos, new Vector3());
        const camSysBefore = fo.toSystem(camera, new Vector3());
        const velBefore = ship.vel.clone();
        const hitBefore = radialHit();
        fo.rebaseAround(ship.currPos, (d) => {
          physics.shiftAll(d.x, d.y, d.z);
          ship.onRebase(d);
          camera.add(d);
          centerLocal.add(d);
          physics.refreshQueries();
        });
        ship.syncFromBody();
        rebases++;
        const posErr = fo.toSystem(ship.currPos, sys).distanceTo(shipSysBefore);
        maxPosErr = Math.max(maxPosErr, posErr);
        expect(posErr).toBeLessThan(1e-3);
        expect(ship.vel.distanceTo(velBefore)).toBeLessThan(1e-9);
        expect(fo.toSystem(camera, sys).distanceTo(camSysBefore)).toBeLessThan(1e-3);
        expect(ship.currPos.length()).toBeLessThan(1024);
        // Collision geometry moved with the origin and is queryable immediately.
        expect(hitBefore).not.toBeNull();
        const hitAfter = radialHit();
        expect(hitAfter).not.toBeNull();
        maxHitErr = Math.max(maxHitErr, hitAfter!.distanceTo(hitBefore!));
        expect(hitAfter!.distanceTo(hitBefore!)).toBeLessThan(1e-3);
      }
    }
    console.log(`rebases=${rebases} maxPosErr=${(maxPosErr * 1000).toFixed(3)}mm maxHitErr=${(maxHitErr * 1000).toFixed(3)}mm colliders=${col.count}`);
    expect(rebases).toBeGreaterThanOrEqual(3);
    // The ship never went through the terrain.
    expect(env.update(ship.currPos).clearance).toBeGreaterThan(0.5);
  }, 240_000);
});
