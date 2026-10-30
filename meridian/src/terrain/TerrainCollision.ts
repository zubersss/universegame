import { Vector3 } from 'three';
import { RAPIER, GROUPS, type Physics } from '../physics/Physics';
import type { BodyDef } from '../world/bodies';
import { chunkAt, chunkKey, dirToFace } from '../world/cube';
import { GRID_INDEX_COUNT, GRID_VERTS, levelSpacing, makeChunkIndex, type ChunkData } from './chunkGen';
import type { ChunkRequest, ChunkStore } from './ChunkStore';
import { BUDGETS } from '../game/config';
import { tangentBasis, type V3 } from '../world/sites';

interface Installed {
  body: RAPIER.RigidBody;
  collider: RAPIER.Collider;
  data: ChunkData;
}

const _p = new Vector3();
const _d = new Vector3();

/**
 * Contact-level triangle-mesh colliders built from the same final terrain
 * triangles that render (no skirts), kept only under the controlled entity and
 * along the ship's predicted path. A smaller residency set than rendering.
 */
export class TerrainCollision {
  private readonly installed = new Map<string, Installed>();
  private readonly gridIndex: Uint32Array;
  /** Keys wanted this update, ordered by urgency. */
  wanted: string[] = [];
  /** Distance along the path for each path key (for readiness). */
  private pathSamples: { key: string; dist: number }[] = [];
  speedLimit = Infinity;
  installsPerFrame = 2;
  changed = false;
  private readonly chunkSize: number;
  /** Max-level keys around the focus (must be present to walk/land). */
  focusKeys: string[] = [];
  /**
   * Extra radius [m] of max-level tiles kept around the focus near the ground,
   * after the 3x3 block and the path corridor (e.g. an on-foot blink range so
   * targets are loaded before they are chosen); 0 keeps just the block. Up to
   * ~150 m fits the collider budget with room for the corridor.
   */
  reach = 0;
  private reachCache: { key: string; keys: string[] } = { key: '', keys: [] };

  constructor(
    private readonly physics: Physics,
    readonly def: BodyDef,
    private readonly store: ChunkStore,
  ) {
    this.gridIndex = new Uint32Array(makeChunkIndex().subarray(0, GRID_INDEX_COUNT));
    this.chunkSize = levelSpacing(def, def.maxLevel) * 32;
  }

  get count(): number {
    return this.installed.size;
  }

  keyForDir(x: number, y: number, z: number): string {
    const f = dirToFace(x, y, z);
    const c = chunkAt(f.face, f.u, f.v, this.def.maxLevel);
    return chunkKey(f.face, this.def.maxLevel, c.x, c.y);
  }

  has(key: string): boolean {
    return this.installed.has(key);
  }

  /**
   * Compute the wanted residency set.
   * @param focusPlanet controlled entity position relative to the planet center
   * @param vel velocity (m/s)
   * @param clearance height above terrain
   * @param decel available deceleration for the stopping distance
   */
  computeWanted(focusPlanet: Vector3, vel: Vector3, clearance: number, decel: number): ChunkRequest[] {
    const keys: string[] = [];
    const add = (k: string) => {
      if (!keys.includes(k)) keys.push(k);
    };
    const n = _d.copy(focusPlanet).normalize();
    const dir: V3 = [n.x, n.y, n.z];
    const basis = tangentBasis(dir);
    const R = this.def.radius;
    const near = clearance < 400;
    this.focusKeys = [];
    if (near) {
      // 3x3 block around the focus.
      const s = this.chunkSize * 0.7;
      for (let j = -1; j <= 1; j++) {
        for (let i = -1; i <= 1; i++) {
          const k = (s * Math.sqrt(i * i + j * j)) / R;
          const l = Math.sqrt(i * i + j * j) || 1;
          const c = i / l;
          const sn = j / l;
          const x = dir[0] + k * (c * basis[0][0] + sn * basis[1][0]);
          const y = dir[1] + k * (c * basis[0][1] + sn * basis[1][1]);
          const z = dir[2] + k * (c * basis[0][2] + sn * basis[1][2]);
          const key = this.keyForDir(x, y, z);
          add(key);
          if (i === 0 && j === 0) this.focusKeys.unshift(key);
          else if (!this.focusKeys.includes(key)) this.focusKeys.push(key);
        }
      }
    }
    // Corridor along the predicted path (charter: speed x 2 s + braking
    // distance + 50 m ahead, and never less than the stop + 250 m margin).
    this.pathSamples = [];
    const speed = vel.length();
    if (speed > 2) {
      const stop = (speed * speed) / (2 * decel);
      const ahead = Math.max(stop + 250, speed * 2 + stop + 50);
      if (clearance < ahead) {
        const len = Math.min(ahead, 4000);
        const stepLen = this.chunkSize * 0.5;
        for (let s = stepLen; s <= len; s += stepLen) {
          _p.copy(focusPlanet).addScaledVector(vel, s / speed);
          const key = this.keyForDir(_p.x, _p.y, _p.z);
          this.pathSamples.push({ key, dist: s });
          add(key);
          if (keys.length >= BUDGETS.maxTerrainColliders) break;
        }
      }
    }
    if (near && this.reach > 0) for (const k of this.reachKeys(dir, basis)) add(k);
    this.wanted = keys.slice(0, BUDGETS.maxTerrainColliders);
    const reqs: ChunkRequest[] = [];
    this.wanted.forEach((k, i) => {
      if (this.store.has(k)) return;
      const [face, level, x, y] = k.split('/').map(Number);
      reqs.push({ key: k, bodyId: this.def.id, face, level, x, y, priority: i });
    });
    return reqs;
  }

  /**
   * Tiles under the reach disc, nearest first: rings a half tile apart out to
   * half a tile beyond the reach, samples a quarter tile apart, so tile
   * corners at the edge of the range are not missed. Cached per focus tile.
   */
  private reachKeys(dir: V3, basis: [V3, V3]): string[] {
    const cacheKey = `${this.keyForDir(dir[0], dir[1], dir[2])}:${this.reach}`;
    if (cacheKey === this.reachCache.key) return this.reachCache.keys;
    const keys: string[] = [];
    const seen = new Set<string>();
    const R = this.def.radius;
    const s = this.chunkSize * 0.5;
    const outer = this.reach + s;
    for (let i = 1; ; i++) {
      const rr = Math.min(i * s, outer);
      const n = Math.max(8, Math.ceil((2 * Math.PI * rr) / (s * 0.5)));
      const k = rr / R;
      for (let j = 0; j < n; j++) {
        const a = (2 * Math.PI * j) / n;
        const c = Math.cos(a) * k;
        const sn = Math.sin(a) * k;
        const key = this.keyForDir(
          dir[0] + c * basis[0][0] + sn * basis[1][0],
          dir[1] + c * basis[0][1] + sn * basis[1][1],
          dir[2] + c * basis[0][2] + sn * basis[1][2],
        );
        if (!seen.has(key)) {
          seen.add(key);
          keys.push(key);
        }
      }
      if (rr >= outer) break;
    }
    this.reachCache = { key: cacheKey, keys };
    return keys;
  }

  /** Install/remove colliders within the per-frame budget. */
  update(planetLocal: Vector3): void {
    let installs = this.installsPerFrame;
    for (const k of this.wanted) {
      if (installs <= 0) break;
      if (this.installed.has(k)) continue;
      const d = this.store.get(k);
      if (!d) continue;
      this.install(k, d, planetLocal);
      installs--;
    }
    // Remove colliders no longer wanted, but only once the focus tiles exist
    // (old coverage stays until replacement coverage is installed).
    const focusReady = this.focusKeys.every((k) => this.installed.has(k));
    if (focusReady || this.installed.size > BUDGETS.maxTerrainColliders) {
      const want = new Set(this.wanted);
      for (const [k, inst] of this.installed) {
        if (!want.has(k)) {
          this.physics.world.removeRigidBody(inst.body);
          this.installed.delete(k);
          this.changed = true;
        }
      }
    }
    if (this.changed) {
      this.physics.refreshQueries();
      this.changed = false;
    }
    this.updateReadiness();
  }

  private install(key: string, d: ChunkData, planetLocal: Vector3): void {
    const world = this.physics.world;
    const body = world.createRigidBody(
      RAPIER.RigidBodyDesc.fixed().setTranslation(planetLocal.x + d.center[0], planetLocal.y + d.center[1], planetLocal.z + d.center[2]),
    );
    const desc = RAPIER.ColliderDesc.trimesh(d.positions.subarray(0, GRID_VERTS * 3), this.gridIndex, RAPIER.TriMeshFlags.FIX_INTERNAL_EDGES)
      .setCollisionGroups(GROUPS.terrain)
      .setSolverGroups(GROUPS.terrain)
      .setFriction(0.9)
      .setRestitution(0);
    const collider = world.createCollider(desc, body);
    this.installed.set(key, { body, collider, data: d });
    this.changed = true;
  }

  private updateReadiness(): void {
    let limit = Infinity;
    for (const s of this.pathSamples) {
      if (!this.installed.has(s.key)) {
        // Allowed speed so the ship can stop before reaching missing data.
        limit = Math.sqrt(2 * 30 * Math.max(0, s.dist - 60));
        break;
      }
    }
    this.speedLimit = limit;
  }

  /** True when the tile under a planet-relative point has a collider. */
  readyAt(pPlanet: Vector3): boolean {
    return this.installed.has(this.keyForDir(pPlanet.x, pPlanet.y, pPlanet.z));
  }

  get focusReady(): boolean {
    return this.focusKeys.length > 0 && this.focusKeys.every((k) => this.installed.has(k));
  }

  installedKeys(): Set<string> {
    return new Set(this.installed.keys());
  }

  /** Remove every collider (body switch). */
  clear(): void {
    for (const inst of this.installed.values()) this.physics.world.removeRigidBody(inst.body);
    this.installed.clear();
    this.wanted = [];
    this.pathSamples = [];
    this.focusKeys = [];
    this.physics.refreshQueries();
  }
}
