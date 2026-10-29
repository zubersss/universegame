import { Frustum, Matrix4, Vector3, type MeshStandardMaterial, type PerspectiveCamera } from 'three';
import type { BodyDef } from './bodies';
import { computeSites, type MissionSites } from './sites';
import { getSurface, type SurfaceGenerator, type SurfaceInfo } from './surface';
import { TerrainManager, type TerrainView } from '../terrain/TerrainManager';
import { TerrainCollision } from '../terrain/TerrainCollision';
import type { ChunkStore } from '../terrain/ChunkStore';
import type { Physics } from '../physics/Physics';
import { PropSystem } from '../props/PropSystem';

const _m = new Matrix4();

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
  private readonly info: SurfaceInfo = { height: 0, biome: 0, variation: 0, special: 0, rockiness: 0 };

  constructor(
    readonly def: BodyDef,
    store: ChunkStore,
    materials: MeshStandardMaterial[],
    physics: Physics,
    aerialSteps: number,
  ) {
    this.sites = computeSites(def);
    this.gen = getSurface(def, this.sites.clearings);
    store.setBody(def.id);
    this.terrain = new TerrainManager(def, store, materials);
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
  }

  /** Terrain height above the datum for a unit direction from the body center. */
  heightAt(dir: Vector3): number {
    return this.gen.height(dir.x, dir.y, dir.z);
  }

  surfaceInfo(dir: Vector3): SurfaceInfo {
    return this.gen.info(dir.x, dir.y, dir.z, this.info);
  }

  /**
   * Per-frame terrain work: LOD selection (throttled), geomorphs, horizon
   * culling and collider installation.
   */
  update(dt: number, camera: PerspectiveCamera, planetLocal: Vector3, focusLocal: Vector3, viewportH: number, nearGround: boolean): void {
    const v = this.view;
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
    this.terrain.cullMeshes(v);
    this.collision.update(planetLocal);
    this.props.update(dt, v.focusPlanet, v.camPlanet, planetLocal, nearGround);
  }

  dispose(): void {
    this.props.dispose();
    this.terrain.dispose();
    this.collision.clear();
  }
}
