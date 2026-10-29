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
import type { BodyDef, BodyId } from './bodies';
import type { MissionSites } from './sites';
import type { SurfaceGenerator } from './surface';
import { GROUPS, type Physics } from '../physics/Physics';
import { patchAerial } from '../render/Atmosphere';
import { hashCombine, hashFloat } from '../core/rng';

// The survey relay mast and the sample deposits of the active body. Built from
// the deterministic mission sites; sample visibility follows the collected IDs.

export interface MissionTarget {
  id: string;
  kind: 'relay' | 'sample';
  /** Planet-relative position of the interaction/scan point. */
  pos: Vector3;
  up: Vector3;
  /** Scan/aim radius (m). */
  radius: number;
}

const _q = new Quaternion();
const _Y = new Vector3(0, 1, 0);

const SAMPLE_LOOK: Record<BodyId, { core: number; glow: number; base: number; name: string }> = {
  ilex: { core: 0xe9e3cf, glow: 0x5fd0b4, base: 0x8a7a58, name: 'Chalk nodule' },
  vesper: { core: 0xb04a2a, glow: 0xffa060, base: 0x2a2224, name: 'Oxide geode' },
  cairn: { core: 0xcfe6ff, glow: 0x7fc4ff, base: 0x6d7178, name: 'Rime core' },
};

export function sampleName(body: BodyId): string {
  return SAMPLE_LOOK[body].name;
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

export class MissionObjects {
  readonly group = new Group();
  readonly targets: MissionTarget[] = [];
  private readonly sampleMeshes = new Map<string, Group>();
  private readonly materials: Material[] = [];
  private readonly geometries: BufferGeometry[] = [];
  private readonly lampMat: MeshStandardMaterial;
  private readonly ring: Mesh;
  private relayCollider: RAPIER.RigidBody | null = null;
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
    const place = (dir: readonly number[], sink: number, yaw: number, obj: Group) => {
      const up = new Vector3(dir[0], dir[1], dir[2]);
      const h = gen.height(up.x, up.y, up.z);
      obj.position.copy(up).multiplyScalar(R + h - sink);
      _q.setFromUnitVectors(_Y, up);
      obj.quaternion.copy(_q).multiply(new Quaternion().setFromAxisAngle(_Y, yaw));
      return up;
    };

    // Relay mast.
    const rg = relayGeometry();
    this.geometries.push(rg.body, rg.metal, rg.dark, rg.ring, rg.lamp);
    const relay = new Group();
    this.lampMat = mat(0x2a2014, 0.4, 0, 0x6a3a10);
    relay.add(
      new Mesh(rg.body, mat(0xe7e2d6, 0.45, 0)),
      new Mesh(rg.metal, mat(0xb07a3c, 0.35, 0.85)),
      new Mesh(rg.dark, mat(0x2b2d31, 0.6, 0.3)),
      new Mesh(rg.lamp, this.lampMat),
    );
    this.ring = new Mesh(rg.ring, mat(0xb07a3c, 0.35, 0.85));
    this.ring.position.y = 6.45;
    relay.add(this.ring);
    for (const m of relay.children) {
      m.castShadow = true;
      m.receiveShadow = true;
    }
    const relayUp = place(sites.relay.dir, 0.05, hashFloat(hashCombine(def.seed, 'relay-yaw')) * Math.PI * 2, relay);
    this.group.add(relay);
    this.targets.push({ id: sites.relay.id, kind: 'relay', pos: relay.position.clone().addScaledVector(relayUp, 3.2), up: relayUp, radius: 1.6 });
    // Fixed capsule so the mast blocks walking and landing.
    const c = relay.position.clone().addScaledVector(relayUp, 3.6);
    this.relayPlanet = c;
    this.relayQuat = relay.quaternion.clone();

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

  private readonly relayPlanet: Vector3;
  private readonly relayQuat: Quaternion;

  /** Show the deposits that have not been collected and light the relay if active. */
  sync(isCollected: (id: string) => boolean, relayActive: boolean): void {
    for (const [id, g] of this.sampleMeshes) g.visible = !isCollected(id);
    this.active = relayActive;
    if (relayActive) {
      this.lampMat.emissive.setHex(0x3fe0c0);
      this.lampMat.emissiveIntensity = 2.2;
    } else {
      this.lampMat.emissive.setHex(0x6a3a10);
      this.lampMat.emissiveIntensity = 1;
    }
  }

  /** Install the relay collider (local coordinates follow the body center). */
  installCollider(planetLocal: Vector3): void {
    this.removeCollider();
    const p = this.relayPlanet.clone().add(planetLocal);
    const q = this.relayQuat;
    const body = this.physics.world.createRigidBody(
      RAPIER.RigidBodyDesc.fixed().setTranslation(p.x, p.y, p.z).setRotation({ x: q.x, y: q.y, z: q.z, w: q.w }),
    );
    const desc = RAPIER.ColliderDesc.capsule(3.4, 0.45).setCollisionGroups(GROUPS.props).setSolverGroups(GROUPS.props);
    this.physics.world.createCollider(desc, body);
    this.relayCollider = body;
    this.physics.refreshQueries();
  }

  removeCollider(): void {
    if (!this.relayCollider) return;
    this.physics.world.removeRigidBody(this.relayCollider);
    this.relayCollider = null;
  }

  get hasCollider(): boolean {
    return this.relayCollider !== null;
  }

  update(dt: number, planetLocal: Vector3): void {
    this.time += dt;
    this.group.position.copy(planetLocal);
    this.ring.rotation.y = this.active ? this.time * 0.6 : 0.4;
    if (this.active) this.lampMat.emissiveIntensity = 1.8 + Math.sin(this.time * 2.2) * 0.5;
  }

  dispose(): void {
    this.removeCollider();
    for (const g of this.geometries) g.dispose();
    for (const m of this.materials) m.dispose();
    this.group.clear();
  }
}

export const MISSION_COLOR = new Color(0x74c6b8);
