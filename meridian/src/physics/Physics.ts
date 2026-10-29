import RAPIER from '@dimforge/rapier3d-compat';
import { SIM_DT } from '../game/config';

export { RAPIER };

/** Collision group bits. */
export const GROUP = {
  TERRAIN: 1 << 0,
  SHIP: 1 << 1,
  PLAYER: 1 << 2,
  PROPS: 1 << 3,
} as const;

/** Rapier interaction groups: 16-bit membership in the high half, filter in the low half. */
export function groups(membership: number, filter: number): number {
  return (((membership & 0xffff) << 16) | (filter & 0xffff)) >>> 0;
}

export const GROUPS = {
  terrain: groups(GROUP.TERRAIN, GROUP.SHIP | GROUP.PLAYER | GROUP.PROPS),
  props: groups(GROUP.PROPS, GROUP.SHIP | GROUP.PLAYER),
  ship: groups(GROUP.SHIP, GROUP.TERRAIN | GROUP.PROPS | GROUP.PLAYER),
  player: groups(GROUP.PLAYER, GROUP.TERRAIN | GROUP.PROPS | GROUP.SHIP),
  /** Query filter: static world only (terrain + props). */
  queryStatic: groups(0xffff, GROUP.TERRAIN | GROUP.PROPS),
  queryTerrain: groups(0xffff, GROUP.TERRAIN),
  /** Query filter used for walking/exit checks (terrain, props, ship). */
  queryWalk: groups(0xffff, GROUP.TERRAIN | GROUP.PROPS | GROUP.SHIP),
} as const;

let initPromise: Promise<void> | null = null;

/** Initialize the Rapier WASM module exactly once. */
export function initPhysics(): Promise<void> {
  if (!initPromise) initPromise = RAPIER.init();
  return initPromise;
}

const REFRESH_DT = 1e-6;

/** Rapier length unit: its dynamic speed clamp is 400 m/s per unit (2,000 m/s here). */
export const PHYSICS_LENGTH_UNIT = 5;

/**
 * Thin wrapper around a Rapier world. World gravity is zero: every entity
 * applies its own radial gravity explicitly.
 */
export class Physics {
  readonly world: RAPIER.World;
  /** Count of query refreshes performed (diagnostics). */
  refreshCount = 0;

  constructor() {
    this.world = new RAPIER.World({ x: 0, y: 0, z: 0 });
    this.world.timestep = SIM_DT;
    // Rapier clamps dynamic body speed to 400 m/s per length unit, but space
    // flight needs 1,800 m/s. Raise the unit and scale the normalized contact
    // tolerances down so the absolute tolerances stay at their defaults.
    const ip = this.world.integrationParameters;
    const err = ip.normalizedAllowedLinearError;
    const pred = ip.normalizedPredictionDistance;
    this.world.lengthUnit = PHYSICS_LENGTH_UNIT;
    ip.normalizedAllowedLinearError = err / PHYSICS_LENGTH_UNIT;
    ip.normalizedPredictionDistance = pred / PHYSICS_LENGTH_UNIT;
  }

  step(): void {
    this.world.step();
  }

  /**
   * Make moved/new colliders visible to scene queries immediately.
   * Rapier 0.21 only refreshes its query BVH during a step, and a zero-dt
   * step is skipped, so we run a 1 µs step with all dynamic velocities
   * zeroed and then restore them (no measurable displacement; world gravity
   * is zero). Must not be called while kinematic bodies have pending targets.
   */
  refreshQueries(): void {
    const saved: { b: RAPIER.RigidBody; v: RAPIER.Vector; w: RAPIER.Vector }[] = [];
    this.world.forEachRigidBody((b) => {
      if (b.isDynamic() && b.isEnabled()) {
        saved.push({ b, v: b.linvel(), w: b.angvel() });
        b.setLinvel({ x: 0, y: 0, z: 0 }, false);
        b.setAngvel({ x: 0, y: 0, z: 0 }, false);
      }
    });
    this.world.timestep = REFRESH_DT;
    this.world.step();
    this.world.timestep = SIM_DT;
    for (const s of saved) {
      s.b.setLinvel(s.v, false);
      s.b.setAngvel(s.w, false);
    }
    this.refreshCount++;
  }

  /** Translate every rigid body by (dx,dy,dz) for an origin rebase. */
  shiftAll(dx: number, dy: number, dz: number): void {
    this.world.forEachRigidBody((b) => {
      const t = b.translation();
      b.setTranslation({ x: t.x + dx, y: t.y + dy, z: t.z + dz }, false);
    });
    this.world.propagateModifiedBodyPositionsToColliders();
  }

  castRay(
    ox: number, oy: number, oz: number,
    dx: number, dy: number, dz: number,
    maxToi: number,
    filterGroups: number = GROUPS.queryStatic,
    exclude?: RAPIER.RigidBody,
  ): { toi: number; nx: number; ny: number; nz: number; collider: RAPIER.Collider } | null {
    const ray = new RAPIER.Ray({ x: ox, y: oy, z: oz }, { x: dx, y: dy, z: dz });
    const hit = this.world.castRayAndGetNormal(ray, maxToi, true, undefined, filterGroups, undefined, exclude);
    if (!hit) return null;
    return { toi: hit.timeOfImpact, nx: hit.normal.x, ny: hit.normal.y, nz: hit.normal.z, collider: hit.collider };
  }

  get bodyCount(): number {
    let n = 0;
    this.world.forEachRigidBody(() => n++);
    return n;
  }

  get colliderCount(): number {
    let n = 0;
    this.world.forEachCollider(() => n++);
    return n;
  }
}
