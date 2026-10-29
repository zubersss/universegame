import { beforeAll, describe, expect, it } from 'vitest';
import { Vector3 } from 'three';
import { initPhysics, Physics } from '../src/physics/Physics';
import { Player, FOOT_OFFSET, type WalkInput } from '../src/player/Player';
import { BODIES } from '../src/world/bodies';
import { computeSites, offsetDir, tangentBasis } from '../src/world/sites';
import { getSurface } from '../src/world/surface';
import { FloatingOrigin } from '../src/core/origin';
import { ChunkStore } from '../src/terrain/ChunkStore';
import { TerrainCollision } from '../src/terrain/TerrainCollision';
import { SIM_DT, WALK } from '../src/game/config';
import { FakeBackend } from './fakeBackend';

beforeAll(async () => {
  await initPhysics();
});

const IDLE: WalkInput = { forward: 0, right: 0, sprint: false, jump: false, yaw: 0, pitch: 0 };

describe('on-foot locomotion on a spherical planet', () => {
  it('walks across tiles and through a rebase, jumps, and stands without drift or sinking', () => {
    const def = BODIES.ilex;
    const sites = computeSites(def);
    const gen = getSurface(def, sites.clearings);
    const physics = new Physics();
    const fo = new FloatingOrigin();
    const n = new Vector3(...sites.landing.dir);
    const ground = new Vector3(...def.center).addScaledVector(n, def.radius + gen.height(n.x, n.y, n.z));
    // Origin placed so a ~2 km walk crosses the rebase threshold.
    const fwd = new Vector3(0, 1, 0).cross(n).normalize();
    FloatingOrigin.rounded(ground.clone().addScaledVector(fwd, -1500), fo.origin);
    const centerLocal = new Vector3(...def.center).sub(fo.origin);
    const store = new ChunkStore(new FakeBackend(), def.id);
    store.maxInFlight = 8;
    const col = new TerrainCollision(physics, def, store);
    const feed = (p: Player) => {
      const fp = p.pos.clone().sub(centerLocal);
      store.setDemand(col.computeWanted(fp, p.vel, 0, 50));
      for (let k = 0; k < 6; k++) (store as unknown as { backend: FakeBackend }).backend.tick();
      col.update(centerLocal);
    };
    const start = ground.clone().sub(fo.origin).addScaledVector(n, FOOT_OFFSET + 0.05);
    const player = new Player(physics, start, n, fwd);
    // Prepare collision under the player before simulating.
    for (let i = 0; i < 20; i++) feed(player);
    expect(col.focusReady).toBe(true);
    physics.refreshQueries();

    const heightAbove = () => {
      const feet = player.feet(new Vector3()).sub(centerLocal);
      const r = feet.length();
      feet.divideScalar(r);
      return r - (def.radius + gen.height(feet.x, feet.y, feet.z));
    };
    let rebases = 0;
    const tiles = new Set<string>();
    let worst = 0;
    let jumped = false;
    let maxJump = 0;
    const step = (input: WalkInput) => {
      if (rebases === 0 || player.stepDistance % 1 < 0.2) feed(player);
      const g = def.gravity;
      player.step(SIM_DT, input, centerLocal, g);
      physics.step();
      if (fo.needsRebase(player.pos)) {
        fo.rebaseAround(player.pos, (d) => {
          physics.shiftAll(d.x, d.y, d.z);
          player.onRebase(d);
          centerLocal.add(d);
          physics.refreshQueries();
        });
        rebases++;
      }
      const fp = player.pos.clone().sub(centerLocal);
      tiles.add(col.keyForDir(fp.x, fp.y, fp.z));
    };
    // Settle.
    for (let i = 0; i < 60; i++) step(IDLE);
    expect(player.grounded).toBe(true);
    // Gap between the feet and the actual contact mesh (rendered contact tiles
    // use these exact triangles), measured with a raycast.
    const meshGap = () => {
      const up = player.up;
      const o = player.feet(new Vector3()).addScaledVector(up, 1);
      const h = physics.castRay(o.x, o.y, o.z, -up.x, -up.y, -up.z, 5, undefined, player.body);
      return h ? h.toi - 1 : Infinity;
    };
    let analyticWorst = 0;
    let nextStop = 300;
    const stops: number[] = [];
    // Sprint ~2 km (with a jump halfway) keeping a straight heading; stop
    // every ~300 m to measure contact at rest.
    for (let i = 0; i < 60 * 300 && player.stepDistance < 2100; i++) {
      const jump = !jumped && player.stepDistance > 900 && player.grounded;
      if (jump) jumped = true;
      step({ forward: 1, right: 0, sprint: true, jump, yaw: 0, pitch: 0 });
      if (jumped && !player.grounded) maxJump = Math.max(maxJump, heightAbove());
      if (player.grounded) analyticWorst = Math.max(analyticWorst, Math.abs(heightAbove()));
      expect(heightAbove()).toBeGreaterThan(-0.2); // never sinks into the ground
      if (player.stepDistance > nextStop) {
        nextStop += 300;
        for (let k = 0; k < 45; k++) step(IDLE);
        const g = meshGap();
        stops.push(g);
        worst = Math.max(worst, Math.abs(g));
      }
    }
    console.log(`contact gaps at rest (cm): ${stops.map((g) => (g * 100).toFixed(1)).join(', ')}; analytic surface deviation max ${(analyticWorst * 100).toFixed(1)} cm`);
    expect(stops.length).toBeGreaterThanOrEqual(5);
    expect(player.stepDistance).toBeGreaterThan(1900);
    expect(rebases).toBeGreaterThanOrEqual(1);
    expect(tiles.size).toBeGreaterThan(15);
    expect(jumped).toBe(true);
    expect(maxJump).toBeGreaterThan(1.0); // 5 m/s jump under 6 m/s^2 ≈ 2 m apex
    // Visual/contact disagreement at tested contact points stays within 0.15 m.
    expect(worst).toBeLessThan(0.15);
    // Stand still: no drift, no sinking.
    for (let i = 0; i < 60; i++) step(IDLE);
    const sysBefore = player.pos.clone().add(fo.origin);
    const hBefore = heightAbove();
    for (let i = 0; i < 300; i++) step(IDLE);
    const drift = player.pos.clone().add(fo.origin).distanceTo(sysBefore);
    expect(drift).toBeLessThan(0.01);
    expect(Math.abs(heightAbove() - hBefore)).toBeLessThan(0.005);
    console.log(`walk: ${player.stepDistance.toFixed(0)} m, tiles=${tiles.size}, rebases=${rebases}, worstContact=${(worst * 100).toFixed(1)} cm, jumpApex=${maxJump.toFixed(2)} m, drift=${(drift * 1000).toFixed(2)} mm`);
    void WALK;
  }, 300_000);
  it('stands still without creeping on varied slopes', () => {
    const def = BODIES.ilex;
    const sites = computeSites(def);
    const gen = getSurface(def, sites.clearings);
    const basis = tangentBasis(sites.landing.dir);
    let worstDrift = 0;
    let worstGap = 0;
    let minGap = Infinity;
    for (let k = 0; k < 12; k++) {
      const ang = k * 1.7;
      const d = offsetDir(sites.landing.dir, basis, Math.cos(ang), Math.sin(ang), 300 + k * 260, def.radius);
      const n = new Vector3(...d);
      const physics = new Physics();
      const fo = new FloatingOrigin();
      const ground = new Vector3(...def.center).addScaledVector(n, def.radius + gen.height(n.x, n.y, n.z));
      FloatingOrigin.rounded(ground, fo.origin);
      const centerLocal = new Vector3(...def.center).sub(fo.origin);
      const store = new ChunkStore(new FakeBackend(), def.id);
      store.maxInFlight = 8;
      const col = new TerrainCollision(physics, def, store);
      const player = new Player(physics, ground.clone().sub(fo.origin).addScaledVector(n, FOOT_OFFSET + 0.05), n, new Vector3(1, 0, 0));
      for (let i = 0; i < 20; i++) {
        store.setDemand(col.computeWanted(player.pos.clone().sub(centerLocal), player.vel, 0, 50));
        for (let j = 0; j < 6; j++) (store as unknown as { backend: FakeBackend }).backend.tick();
        col.update(centerLocal);
      }
      physics.refreshQueries();
      for (let i = 0; i < 90; i++) {
        player.step(SIM_DT, IDLE, centerLocal, def.gravity);
        physics.step();
      }
      expect(player.grounded).toBe(true);
      const p0 = player.pos.clone();
      for (let i = 0; i < 180; i++) {
        player.step(SIM_DT, IDLE, centerLocal, def.gravity);
        physics.step();
      }
      worstDrift = Math.max(worstDrift, player.pos.distanceTo(p0));
      const feet = player.feet(new Vector3()).sub(centerLocal);
      const r = feet.length();
      feet.divideScalar(r);
      const gap = r - (def.radius + gen.height(feet.x, feet.y, feet.z));
      worstGap = Math.max(worstGap, gap);
      minGap = Math.min(minGap, gap);
    }
    console.log(`idle 3 s at 12 sites: worst drift ${(worstDrift * 1000).toFixed(3)} mm, contact gap ${(minGap * 100).toFixed(1)}..${(worstGap * 100).toFixed(1)} cm`);
    expect(worstDrift).toBeLessThan(0.0005);
    expect(minGap).toBeGreaterThan(-0.01);
    expect(worstGap).toBeLessThan(0.08);
  });
});
