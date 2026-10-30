import {
  BufferGeometry,
  Color,
  CylinderGeometry,
  Group,
  IcosahedronGeometry,
  Mesh,
  MeshStandardMaterial,
  OctahedronGeometry,
  Quaternion,
  SphereGeometry,
  TorusGeometry,
  Vector3,
  type Material,
} from 'three';
import RAPIER from '@dimforge/rapier3d-compat';
import { mergeGeometries } from 'three/addons/utils/BufferGeometryUtils.js';
import type { BodyDef, BodyId, DataTag } from './bodies';
import type { MissionSites } from './sites';
import { newSurfaceInfo, type SurfaceGenerator } from './surface';
import { GROUPS, type Physics } from '../physics/Physics';
import { patchAerial } from '../render/Atmosphere';
import { hashCombine, hashFloat } from '../core/rng';

// Mission objects of the active body, built from the deterministic mission
// sites. Quiet System: the survey relay mast and the sample deposits (sample
// visibility follows the collected IDs). Sol: First Light route beacons (lamp
// lit once reached) and the scan targets (landmarks, no mesh).

export interface MissionTarget {
  id: string;
  kind: 'relay' | 'sample' | 'route' | 'scan';
  /** Planet-relative position of the interaction/scan point. */
  pos: Vector3;
  up: Vector3;
  /** Scan/aim radius (m). */
  radius: number;
  /** Display name (route waypoints and scan targets). */
  label?: string;
  /** Route waypoints: reached when the controlled entity is within this distance [m]. */
  arrive?: number;
  /** Scan targets: journal text and data tag. */
  note?: string;
  tag?: DataTag;
}

const _q = new Quaternion();
const _Y = new Vector3(0, 1, 0);

const SAMPLE_LOOK: Record<BodyId, { core: number; glow: number; base: number; name: string }> = {
  ilex: { core: 0xe9e3cf, glow: 0x5fd0b4, base: 0x8a7a58, name: 'Chalk nodule' },
  vesper: { core: 0xb04a2a, glow: 0xffa060, base: 0x2a2224, name: 'Oxide geode' },
  cairn: { core: 0xcfe6ff, glow: 0x7fc4ff, base: 0x6d7178, name: 'Rime core' },
};

export function sampleName(body: BodyId): string {
  return SAMPLE_LOOK[body]?.name ?? 'Sample';
}

function relayGeometry(): { body: BufferGeometry; metal: BufferGeometry; dark: BufferGeometry; ring: BufferGeometry; lamp: BufferGeometry } {
  const parts = (gs: BufferGeometry[]) => {
    const g = mergeGeometries(gs.map((x) => (x.index ? x.toNonIndexed() : x)), false);
    if (!g) throw new Error('relay merge failed');
    g.computeVertexNormals();
    return g;
  };
  // Ceramic mast on a tripod of graphite legs; warm metal collars.
  const mast = new CylinderGeometry(0.16, 0.26, 6.2, 12);
  mast.translate(0, 3.6, 0);
  const head = new CylinderGeometry(0.42, 0.3, 0.7, 12);
  head.translate(0, 6.9, 0);
  const legs: BufferGeometry[] = [];
  for (let i = 0; i < 3; i++) {
    const a = (i / 3) * Math.PI * 2;
    const leg = new CylinderGeometry(0.07, 0.11, 2.3, 6);
    leg.rotateZ(0.62);
    leg.translate(-0.62, 0.85, 0);
    leg.rotateY(a);
    legs.push(leg);
    const foot = new CylinderGeometry(0.22, 0.26, 0.12, 8);
    foot.translate(-1.22, 0.06, 0);
    foot.rotateY(a);
    legs.push(foot);
  }
  const collar1 = new CylinderGeometry(0.3, 0.3, 0.18, 12);
  collar1.translate(0, 1.2, 0);
  const collar2 = new CylinderGeometry(0.24, 0.24, 0.14, 12);
  collar2.translate(0, 5.2, 0);
  const plate = new CylinderGeometry(0.75, 0.75, 0.06, 20);
  plate.rotateX(0.35);
  plate.translate(0, 6.05, 0.25);
  const ring = new TorusGeometry(0.95, 0.05, 6, 40);
  ring.rotateX(Math.PI / 2);
  ring.translate(0, 0, 0);
  const lamp = new SphereGeometry(0.17, 12, 8);
  lamp.translate(0, 7.38, 0);
  return { body: parts([mast, head]), metal: parts([collar1, collar2, plate]), dark: parts(legs), ring, lamp };
}

function sampleGeometry(body: BodyId): { core: BufferGeometry; base: BufferGeometry } {
  const stones: BufferGeometry[] = [];
  for (let i = 0; i < 5; i++) {
    const s = new IcosahedronGeometry(0.22 + (i % 3) * 0.06, 0);
    const a = (i / 5) * Math.PI * 2;
    s.scale(1, 0.55, 1);
    s.translate(Math.cos(a) * 0.42, 0.06, Math.sin(a) * 0.42);
    stones.push(s);
  }
  const base = mergeGeometries(stones.map((g) => (g.index ? g.toNonIndexed() : g)), false)!;
  base.computeVertexNormals();
  let core: BufferGeometry;
  if (body === 'vesper') {
    const shards = [0, 1, 2, 3].map((i) => {
      const o = new OctahedronGeometry(0.2, 0);
      o.scale(0.6, 1.8, 0.6);
      o.rotateZ((i - 1.5) * 0.35);
      o.rotateY(i * 1.7);
      o.translate((i - 1.5) * 0.08, 0.38, ((i % 2) - 0.5) * 0.12);
      return o.index ? o.toNonIndexed() : o;
    });
    core = mergeGeometries(shards, false)!;
  } else if (body === 'cairn') {
    const c = new CylinderGeometry(0.16, 0.2, 0.9, 6);
    c.translate(0, 0.45, 0);
    const tip = new OctahedronGeometry(0.17, 0);
    tip.translate(0, 0.95, 0);
    core = mergeGeometries([c.index ? c.toNonIndexed() : c, tip.index ? tip.toNonIndexed() : tip], false)!;
  } else {
    const n = new IcosahedronGeometry(0.34, 1);
    n.scale(1, 0.8, 1);
    n.translate(0, 0.32, 0);
    core = n;
  }
  core.computeVertexNormals();
  return { core, base };
}

/** A relay or beacon mast: lamp and ring animate when it is active. */
interface Mast {
  id: string;
  lamp: MeshStandardMaterial;
  ring: Mesh;
  /** Collider capsule centre (planet-relative) and orientation. */
  planet: Vector3;
  quat: Quaternion;
  active: boolean;
}

export class MissionObjects {
  readonly group = new Group();
  readonly targets: MissionTarget[] = [];
  private readonly sampleMeshes = new Map<string, Group>();
  private readonly materials: Material[] = [];
  private readonly geometries: BufferGeometry[] = [];
  private readonly masts: Mast[] = [];
  private colliders: RAPIER.RigidBody[] = [];
  private time = 0;
  active = false;

  constructor(
    readonly def: BodyDef,
    sites: MissionSites,
    gen: SurfaceGenerator,
    private readonly physics: Physics,
    aerialSteps: number,
  ) {
    const R = def.radius;
    const mat = (color: number, rough: number, metal: number, emissive = 0x000000): MeshStandardMaterial => {
      const m = new MeshStandardMaterial({ color, roughness: rough, metalness: metal, emissive });
      patchAerial(m, aerialSteps, undefined, 'mission');
      this.materials.push(m);
      return m;
    };
    const info = newSurfaceInfo();
    /** Ground, or the liquid surface where the site is under water. */
    const groundAt = (up: Vector3) => {
      gen.info(up.x, up.y, up.z, info);
      return Math.max(info.height, info.liquidLevel ?? -Infinity);
    };
    const place = (dir: readonly number[], sink: number, yaw: number, obj: Group) => {
      const up = new Vector3(dir[0], dir[1], dir[2]);
      obj.position.copy(up).multiplyScalar(R + groundAt(up) - sink);
      _q.setFromUnitVectors(_Y, up);
      obj.quaternion.copy(_q).multiply(new Quaternion().setFromAxisAngle(_Y, yaw));
      return up;
    };

    // Relay (Quiet System) or route beacon (Sol) masts.
    const rg = relayGeometry();
    this.geometries.push(rg.body, rg.metal, rg.dark, rg.ring, rg.lamp);
    const bodyMat = mat(0xe7e2d6, 0.45, 0);
    const metalMat = mat(0xb07a3c, 0.35, 0.85);
    const darkMat = mat(0x2b2d31, 0.6, 0.3);
    const mast = (id: string, dir: readonly number[], yawKey: string): { obj: Group; up: Vector3 } => {
      const obj = new Group();
      const lamp = mat(0x2a2014, 0.4, 0, 0x6a3a10);
      const ring = new Mesh(rg.ring, metalMat);
      ring.position.y = 6.45;
      obj.add(new Mesh(rg.body, bodyMat), new Mesh(rg.metal, metalMat), new Mesh(rg.dark, darkMat), new Mesh(rg.lamp, lamp), ring);
      for (const m of obj.children) {
        m.castShadow = true;
        m.receiveShadow = true;
      }
      const up = place(dir, 0.05, hashFloat(hashCombine(def.seed, yawKey)) * Math.PI * 2, obj);
      this.group.add(obj);
      // Fixed capsule so the mast blocks walking and landing.
      this.masts.push({ id, lamp, ring, planet: obj.position.clone().addScaledVector(up, 3.6), quat: obj.quaternion.clone(), active: false });
      return { obj, up };
    };

    if (def.system !== 'quiet') {
      sites.route.forEach((r, i) => {
        const { obj, up } = mast(r.id, r.dir, `route-yaw-${i}`);
        this.targets.push({ id: r.id, kind: 'route', pos: obj.position.clone().addScaledVector(up, 3.2), up, radius: 1.6, label: r.label, arrive: r.radius });
      });
      for (const t of sites.scans) {
        const up = new Vector3(...t.dir);
        const pos = up.clone().multiplyScalar(R + groundAt(up) + 2);
        this.targets.push({ id: t.id, kind: 'scan', pos, up, radius: 4, label: t.label, note: t.note, tag: t.tag });
      }
      return;
    }

    const relay = mast(sites.relay.id, sites.relay.dir, 'relay-yaw');
    this.targets.push({ id: sites.relay.id, kind: 'relay', pos: relay.obj.position.clone().addScaledVector(relay.up, 3.2), up: relay.up, radius: 1.6 });

    // Sample deposits.
    const look = SAMPLE_LOOK[def.id];
    const sg = sampleGeometry(def.id);
    this.geometries.push(sg.core, sg.base);
    const coreMat = mat(look.core, def.id === 'vesper' ? 0.25 : 0.5, def.id === 'vesper' ? 0.2 : 0, look.glow);
    coreMat.emissiveIntensity = 0.55;
    const baseMat = mat(look.base, 0.85, 0);
    for (const s of sites.samples) {
      const g = new Group();
      const core = new Mesh(sg.core, coreMat);
      const base = new Mesh(sg.base, baseMat);
      core.castShadow = true;
      base.receiveShadow = true;
      g.add(base, core);
      const up = place(s.dir, 0.04, hashFloat(hashCombine(def.seed, s.id)) * Math.PI * 2, g);
      this.group.add(g);
      this.sampleMeshes.set(s.id, g);
      this.targets.push({ id: s.id, kind: 'sample', pos: g.position.clone().addScaledVector(up, 0.4), up, radius: 0.7 });
    }
  }

  /**
   * Show the deposits that have not been collected and light the relay if
   * active (Quiet System); light each route beacon once `reached(id)` (Sol).
   */
  sync(isCollected: (id: string) => boolean, relayActive: boolean, reached?: (id: string) => boolean): void {
    for (const [id, g] of this.sampleMeshes) g.visible = !isCollected(id);
    this.active = relayActive;
    for (const m of this.masts) {
      m.active = this.def.system === 'quiet' ? relayActive : (reached?.(m.id) ?? false);
      m.lamp.emissive.setHex(m.active ? 0x3fe0c0 : 0x6a3a10);
      m.lamp.emissiveIntensity = m.active ? 2.2 : 1;
    }
  }

  /** Install the mast colliders (local coordinates follow the body center). */
  installCollider(planetLocal: Vector3): void {
    this.removeCollider();
    for (const m of this.masts) {
      const p = m.planet.clone().add(planetLocal);
      const q = m.quat;
      const body = this.physics.world.createRigidBody(
        RAPIER.RigidBodyDesc.fixed().setTranslation(p.x, p.y, p.z).setRotation({ x: q.x, y: q.y, z: q.z, w: q.w }),
      );
      const desc = RAPIER.ColliderDesc.capsule(3.4, 0.45).setCollisionGroups(GROUPS.props).setSolverGroups(GROUPS.props);
      this.physics.world.createCollider(desc, body);
      this.colliders.push(body);
    }
    this.physics.refreshQueries();
  }

  removeCollider(): void {
    for (const b of this.colliders) this.physics.world.removeRigidBody(b);
    this.colliders = [];
  }

  get hasCollider(): boolean {
    return this.colliders.length > 0;
  }

  update(dt: number, planetLocal: Vector3): void {
    this.time += dt;
    this.group.position.copy(planetLocal);
    for (const m of this.masts) {
      m.ring.rotation.y = m.active ? this.time * 0.6 : 0.4;
      if (m.active) m.lamp.emissiveIntensity = 1.8 + Math.sin(this.time * 2.2) * 0.5;
    }
  }

  dispose(): void {
    this.removeCollider();
    for (const g of this.geometries) g.dispose();
    for (const m of this.materials) m.dispose();
    this.group.clear();
  }
}

export const MISSION_COLOR = new Color(0x74c6b8);
