// W8: surface queries for on-foot play (charter D): groundProbe and
// collisionReady on the active body, and the collision look-ahead
// (speed x 2 s + braking distance + 50 m) in TerrainCollision.computeWanted.
import { beforeAll, describe, expect, it } from 'vitest';
import { MeshStandardMaterial, PerspectiveCamera, Vector3 } from 'three';
import { initPhysics, Physics } from '../src/physics/Physics';
import { ActiveBody } from '../src/world/ActiveBody';
import { BODIES } from '../src/world/bodies';
import { tangentBasis } from '../src/world/sites';
import { ChunkStore } from '../src/terrain/ChunkStore';
import { BUDGETS } from '../src/game/config';
import { FakeBackend } from './fakeBackend';

beforeAll(async () => {
  await initPhysics();
});

/** The Moon's landing site with the ground there at the local origin (camera-centred frame). */
function setup() {
  const def = BODIES.moon;
  const physics = new Physics();
  const backend = new FakeBackend();
  const store = new ChunkStore(backend, def.id);
  store.maxInFlight = 16;
  const body = new ActiveBody(def, store, Array.from({ length: 8 }, () => new MeshStandardMaterial()), physics, 4);
  const up = new Vector3(...body.sites.landing.dir);
  const ground = def.radius + body.heightAt(up);
  const center = up.clone().multiplyScalar(-ground);
  // One frame from orbit hands the body its centre (held by reference) without loading detail.
  const camera = new PerspectiveCamera(60, 16 / 9, 1, 1e7);
  camera.position.copy(up).multiplyScalar(def.radius * 3).add(center);
  camera.lookAt(center);
  camera.updateMatrixWorld();
  body.update(0.2, camera, center, camera.position, 720, false);
  const [t1, t2] = tangentBasis([up.x, up.y, up.z]);
  /** Local point `east` / `north` metres along the tangent plane and `h` above the analytic ground. */
  const at = (e: number, n: number, h: number) => {
    const d = up.clone().addScaledVector(new Vector3(...t1), e / def.radius).addScaledVector(new Vector3(...t2), n / def.radius).normalize();
    return d.multiplyScalar(def.radius + body.heightAt(d) + h).add(center);
  };
  /** Run the collision streaming loop (demand, worker results, installs) around `focus`. */
  const load = (focus: Vector3, vel = new Vector3(), frames = 40) => {
    for (let i = 0; i < frames; i++) {
      store.setDemand(body.collision.computeWanted(focus.clone().sub(center), vel, 0, 50));
      for (let k = 0; k < 4; k++) backend.tick();
      body.collision.update(center);
    }
    physics.refreshQueries();
  };
  return { def, body, center, up, at, load };
}

describe('surface queries (W8)', () => {
  it('groundProbe reads the analytic surface before colliders load and the collider triangles after', () => {
    const { def, body, center, up, at, load } = setup();
    const feet = at(0, 0, 1.2);
    expect(body.collisionReady(feet, 1)).toBe(false);
    const a = body.groundProbe(feet, 10)!;
    expect(a).not.toBeNull();
    const g = up.clone().multiplyScalar(def.radius + body.heightAt(up)).add(center);
    expect(a.point.distanceTo(g)).toBeLessThan(1e-6);
    expect(a.normal.length()).toBeCloseTo(1, 9);
    expect(a.normal.dot(up)).toBeGreaterThan(0.5);
    expect(a.slopeDeg).toBeGreaterThanOrEqual(0);
    expect(a.slopeDeg).toBeLessThan(60);
    // Out of reach above, and the lift catches feet a little below the ground.
    expect(body.groundProbe(at(0, 0, 25), 10)).toBeNull();
    expect(body.groundProbe(at(0, 0, -0.5), 10)!.point.distanceTo(g)).toBeLessThan(1e-6);

    load(feet);
    expect(body.collisionReady(feet, 1)).toBe(true);
    const out = { point: new Vector3(), normal: new Vector3(), slopeDeg: -1 };
    const b = body.groundProbe(feet, 10, out)!;
    expect(b).toBe(out); // no allocation when `out` is given
    // Collider triangles interpolate the same surface: centimetres to decimetres apart, same slope.
    expect(b.point.distanceTo(g)).toBeLessThan(0.5);
    expect(b.normal.dot(up)).toBeGreaterThan(0.5);
    expect(Math.abs(b.slopeDeg - a.slopeDeg)).toBeLessThan(15);
    expect(body.groundProbe(at(0, 0, 25), 10)).toBeNull();
    // Across the loaded block the two paths agree everywhere (walkable ground, same contact).
    let worst = 0;
    let checked = 0;
    for (let i = -4; i <= 4; i++) {
      for (let j = -4; j <= 4; j++) {
        const p = at(i * 6, j * 6, 1.2);
        if (!body.collisionReady(p, 0.5)) continue;
        checked++;
        const h = body.groundProbe(p, 10)!;
        const d = p.clone().sub(center).normalize();
        const ga = d.multiplyScalar(def.radius + body.heightAt(d)).add(center);
        worst = Math.max(worst, h.point.distanceTo(ga));
      }
    }
    expect(checked).toBe(81);
    expect(worst).toBeLessThan(0.5);
  });

  it('collisionReady covers a disc, and reach keeps a blink range loaded', () => {
    const { body, at, load } = setup();
    const feet = at(0, 0, 1.2);
    load(feet);
    expect(body.collisionReady(feet, 20)).toBe(true);
    expect(body.collisionReady(at(400, 0, 1.2), 1)).toBe(false);
    expect(body.collisionReady(feet, 400)).toBe(false);
    // Blink targets in every direction (charter K: Lunar Step 60 m, Anchor Blink 140 m).
    const ring = (m: number) => {
      let n = 0;
      for (let k = 0; k < 16; k++) {
        const a = (k / 16) * Math.PI * 2;
        if (body.collisionReady(at(m * Math.cos(a), m * Math.sin(a), 1.2), 0.5)) n++;
      }
      return n;
    };
    expect(ring(140)).toBeLessThan(16); // the walking block alone does not reach that far
    body.collision.reach = 140;
    load(feet);
    expect(ring(60)).toBe(16);
    expect(ring(140)).toBe(16);
    expect(body.collision.wanted.length).toBeLessThanOrEqual(BUDGETS.maxTerrainColliders);
    // Back to the walking block: the extra tiles are released.
    body.collision.reach = 0;
    load(feet);
    expect(ring(140)).toBeLessThan(16);
    expect(body.collisionReady(feet, 20)).toBe(true);
  });

  it('keeps speed x 2 s + braking distance + 50 m ahead in the wanted set (Redline top speed)', () => {
    const { def, body, center, up, at } = setup();
    const feet = at(0, 0, 1.2);
    const [t1] = tangentBasis([up.x, up.y, up.z]);
    const speed = 110; // charter K: Redline top speed; brake 50 m/s^2
    const vel = new Vector3(...t1).multiplyScalar(speed);
    body.collision.computeWanted(feet.clone().sub(center), vel, 0, 50);
    const ahead = speed * 2 + (speed * speed) / (2 * 50) + 50; // 391 m
    for (let s = 0; s <= ahead - 20; s += 20) {
      const p = feet.clone().sub(center).addScaledVector(vel, s / speed).normalize();
      expect(body.collision.wanted, `${s} m ahead`).toContain(body.collision.keyForDir(p.x, p.y, p.z));
    }
    expect(def.explore).toBe('surface');
  });
});
