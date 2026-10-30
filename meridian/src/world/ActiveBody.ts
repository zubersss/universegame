import { Frustum, Matrix4, Vector3, type MeshStandardMaterial, type PerspectiveCamera } from 'three';
import type { BodyDef } from './bodies';
import { computeSites, type MissionSites } from './sites';
import { getSurface, newSurfaceInfo, type SurfaceGenerator, type SurfaceInfo } from './surface';
import { TerrainManager, type TerrainView } from '../terrain/TerrainManager';
import { TerrainCollision } from '../terrain/TerrainCollision';
import type { ChunkStore } from '../terrain/ChunkStore';
import { GROUPS, type Physics } from '../physics/Physics';
import { PropSystem } from '../props/PropSystem';
import { createWaterMaterial, SEA_WATER, type WaterUniforms } from '../terrain/waterMaterial';
import { levelSpacing, surfaceNormal } from '../terrain/chunkGen';
import { tangentBasis } from './sites';

const _m = new Matrix4();
const _up = new Vector3();
const _rel = new Vector3();
const _n: number[] = [0, 0, 0];

/** Where a probe toward the body centre meets the ground (charter section D, surface queries). */
export interface GroundHit {
  /** Contact point [m, local frame]. */
  point: Vector3;
  /** Unit surface normal at the contact, pointing away from the body. */
  normal: Vector3;
  /** Angle between the normal and local up [deg]. */
  slopeDeg: number;
}

/** groundProbe starts this far above the query point, so feet resting on (or a hair below) the ground still hit it [m]. */
const PROBE_LIFT = 2;

/** Runtime state of the one body that has detailed terrain and collision. */
export class ActiveBody {
  readonly gen: SurfaceGenerator;
  readonly sites: MissionSites;
  readonly terrain: TerrainManager;
  readonly collision: TerrainCollision;
  readonly props: PropSystem;
  private readonly frustum = new Frustum();
  readonly view: TerrainView;
  private lodTimer = 0;
  /** Liquid-surface material (bodies with an ocean or lakes), disposed with the body. */
  private readonly water: { material: MeshStandardMaterial; uniforms: WaterUniforms } | null;
  private readonly info: SurfaceInfo = newSurfaceInfo();
  /** Body centre in the local frame: the vector passed to update(), held by reference (rebases move it in place). */
  private center: Vector3;

  constructor(
    readonly def: BodyDef,
    store: ChunkStore,
    materials: MeshStandardMaterial[],
    private readonly physics: Physics,
    aerialSteps: number,
  ) {
    this.sites = computeSites(def);
    this.gen = getSurface(def, this.sites.clearings);
    store.setBody(def.id);
    this.terrain = new TerrainManager(def, store, materials);
    this.water = def.seaLevel != null ? createWaterMaterial(SEA_WATER, aerialSteps, false) : null;
    this.terrain.waterMaterial = this.water?.material ?? null;
    this.collision = new TerrainCollision(physics, def, store);
    this.props = new PropSystem(def, this.gen, this.sites, physics, aerialSteps);
    this.view = {
      camPlanet: new Vector3(),
      frustum: this.frustum,
      planetLocal: new Vector3(),
      fovY: 1,
      viewportH: 720,
      focusPlanet: new Vector3(),
      contactRadius: 150,
    };
    this.center = this.view.planetLocal;
  }

  /** Terrain height above the datum for a unit direction from the body center. */
  heightAt(dir: Vector3): number {
    return this.gen.height(dir.x, dir.y, dir.z);
  }

  surfaceInfo(dir: Vector3): SurfaceInfo {
    return this.gen.info(dir.x, dir.y, dir.z, this.info);
  }

  /**
   * The ground below `posLocal` (toward the body centre) within `maxDist`
   * metres, or null. Where terrain colliders are installed the probe hits the
   * exact triangles and props the character collides with; elsewhere it reads
   * the analytic surface the meshes are built from (same point to within the
   * mesh's interpolation error). Liquids are not ground: check
   * surfaceInfo(dir).liquidLevel. Pass `out` to avoid allocating.
   */
  groundProbe(posLocal: Vector3, maxDist: number, out?: GroundHit): GroundHit | null {
    if (this.def.explore !== 'surface') return null;
    const c = this.center;
    const up = _up.copy(posLocal).sub(c);
    const r = up.length();
    if (!(r > 0)) return null;
    up.multiplyScalar(1 / r);
    const hit = out ?? { point: new Vector3(), normal: new Vector3(), slopeDeg: 0 };
    if (this.collision.readyAt(_rel.copy(posLocal).sub(c))) {
      const ox = posLocal.x + up.x * PROBE_LIFT;
      const oy = posLocal.y + up.y * PROBE_LIFT;
      const oz = posLocal.z + up.z * PROBE_LIFT;
      const h = this.physics.castRay(ox, oy, oz, -up.x, -up.y, -up.z, maxDist + PROBE_LIFT, GROUPS.queryStatic);
      if (!h) return null;
      hit.point.set(ox - up.x * h.toi, oy - up.y * h.toi, oz - up.z * h.toi);
      hit.normal.set(h.nx, h.ny, h.nz);
      if (hit.normal.dot(up) < 0) hit.normal.negate();
    } else {
      const ground = this.def.radius + this.gen.height(up.x, up.y, up.z);
      const alt = r - ground;
      if (alt > maxDist || alt < -PROBE_LIFT) return null;
      hit.point.copy(up).multiplyScalar(ground).add(c);
      surfaceNormal(this.gen, [up.x, up.y, up.z], levelSpacing(this.def, this.def.maxLevel), _n);
      hit.normal.set(_n[0], _n[1], _n[2]);
      if (hit.normal.dot(up) < 0) hit.normal.negate();
    }
    hit.slopeDeg = (Math.acos(Math.min(1, Math.max(-1, hit.normal.dot(up)))) * 180) / Math.PI;
    return hit;
  }

  /**
   * True when terrain colliders are installed under the whole disc of `radius`
   * metres around the point below `posLocal` (every max-level tile it touches),
   * so physics can take over there. False on bodies without terrain.
   */
  collisionReady(posLocal: Vector3, radius: number): boolean {
    if (this.def.explore !== 'surface') return false;
    const p = _rel.copy(posLocal).sub(this.center);
    const r = p.length();
    if (!(r > 0)) return false;
    const d: [number, number, number] = [p.x / r, p.y / r, p.z / r];
    const col = this.collision;
    if (!col.has(col.keyForDir(d[0], d[1], d[2]))) return false;
    // Rings every half tile out to the radius, samples at most a quarter tile apart.
    const [t1, t2] = tangentBasis(d);
    const R = this.def.radius;
    const step = levelSpacing(this.def, this.def.maxLevel) * 16;
    const rings = Math.max(1, Math.ceil(Math.max(0, radius) / step));
    for (let i = 1; i <= rings; i++) {
      const rr = Math.min(radius, i * step);
      const n = Math.max(8, Math.ceil((4 * Math.PI * rr) / step));
      const k = rr / R;
      for (let j = 0; j < n; j++) {
        const a = (2 * Math.PI * j) / n;
        const ca = Math.cos(a) * k;
        const sa = Math.sin(a) * k;
        if (!col.has(col.keyForDir(d[0] + ca * t1[0] + sa * t2[0], d[1] + ca * t1[1] + sa * t2[1], d[2] + ca * t1[2] + sa * t2[2]))) return false;
      }
    }
    return true;
  }

  /**
   * Per-frame terrain work: LOD selection (throttled), geomorphs, horizon
   * culling and collider installation.
   */
  update(dt: number, camera: PerspectiveCamera, planetLocal: Vector3, focusLocal: Vector3, viewportH: number, nearGround: boolean): void {
    const v = this.view;
    this.center = planetLocal;
    v.planetLocal.copy(planetLocal);
    v.camPlanet.copy(camera.position).sub(planetLocal);
    v.focusPlanet.copy(focusLocal).sub(planetLocal);
    v.fovY = (camera.fov * Math.PI) / 180;
    v.viewportH = viewportH;
    _m.multiplyMatrices(camera.projectionMatrix, camera.matrixWorldInverse);
    this.frustum.setFromProjectionMatrix(_m);
    this.terrain.root.position.copy(planetLocal);
    this.lodTimer -= dt;
    if (this.lodTimer <= 0) {
      this.lodTimer = 0.12;
      this.terrain.setContactKeys(this.collision.installedKeys());
      this.terrain.update(v);
    }
    this.terrain.updateMorphs(dt);
    if (this.water) this.water.uniforms.uWaterTime.value += dt;
    this.terrain.cullMeshes(v);
    this.collision.update(planetLocal, dt);
    this.props.update(dt, v.focusPlanet, v.camPlanet, planetLocal, nearGround);
  }

  dispose(): void {
    this.props.dispose();
    this.terrain.dispose();
    this.collision.clear();
    this.water?.material.dispose();
  }
}
