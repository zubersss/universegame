import {
  Color,
  DynamicDrawUsage,
  Group,
  InstancedMesh,
  Matrix4,
  MeshStandardMaterial,
  Quaternion,
  Vector3,
} from 'three';
import type { BodyDef } from '../world/bodies';
import type { SurfaceGenerator, SurfaceInfo } from '../world/surface';
import { chunkAt, chunkBounds, chunkKey, dirToFace, faceDir } from '../world/cube';
import { levelSpacing } from '../terrain/chunkGen';
import { tangentBasis, LANDING_R0, RELAY_R1, type MissionSites, type V3 } from '../world/sites';
import { hashCombine } from '../core/rng';
import { patchAerial } from '../render/Atmosphere';
import { RAPIER, GROUPS, type Physics } from '../physics/Physics';
import { BUDGETS } from '../game/config';
import { speciesFor, type Species } from './species';
import type { SpeciesGeometry } from './propMeshes';

export interface PropInstance {
  id: string;
  species: Species;
  /** Planet-relative base position (double). */
  p: Vector3;
  up: Vector3;
  yaw: number;
  h: number;
  tint: number;
}

/** Shared wind/time uniform for all prop materials. */
export const propUniforms = { uTime: { value: 0 } };

const _m = new Matrix4();
const _q = new Quaternion();
const _qy = new Quaternion();
const _s = new Vector3();
const _v = new Vector3();
const _c = new Color();
const _Y = new Vector3(0, 1, 0);

function hf(h: number, k: number): number {
  return hashCombine(h, k) / 4294967296;
}

/**
 * Deterministic instanced scenery for the active body. Placement comes from a
 * fixed cube-cell grid (the max-level chunk grid) independent of render LOD;
 * instance IDs hash (body, cell, species, candidate).
 */
export class PropSystem {
  readonly group = new Group();
  private readonly species: Species[];
  private readonly geos: SpeciesGeometry[] = [];
  private readonly materials: MeshStandardMaterial[] = [];
  private readonly lod0: InstancedMesh[] = [];
  private readonly lod1: (InstancedMesh | null)[] = [];
  private readonly cells = new Map<string, PropInstance[]>();
  private pending: string[] = [];
  private readonly anchor = new Vector3();
  private readonly lastEnum = new Vector3(1e9, 0, 0);
  private readonly lastFill = new Vector3(1e9, 0, 0);
  private readonly lastCol = new Vector3(1e9, 0, 0);
  private fillDirty = true;
  private fillTimer = 0;
  private readonly cellSize: number;
  private readonly colliders = new Map<string, RAPIER.RigidBody>();
  density = 1;
  rangeScale = 1;
  readonly stats = { cells: 0, instances: 0, drawn: 0, colliders: 0, genMs: 0, pending: 0 };
  private readonly info: SurfaceInfo = { height: 0, biome: 0, variation: 0, special: 0, rockiness: 0 };
  private readonly exclusions: { dir: V3; r: number }[] = [];

  constructor(
    readonly def: BodyDef,
    private readonly gen: SurfaceGenerator,
    sites: MissionSites,
    private readonly physics: Physics,
    aerialSteps: number,
  ) {
    this.group.name = `props-${def.id}`;
    this.species = speciesFor(def.id);
    this.cellSize = levelSpacing(def, def.maxLevel) * 32;
    this.exclusions.push({ dir: sites.landing.dir, r: LANDING_R0 + 8 }, { dir: sites.relay.dir, r: RELAY_R1 + 4 });
    for (const smp of sites.samples) this.exclusions.push({ dir: smp.dir, r: 5 });
    for (const sp of this.species) {
      const g = sp.make();
      this.geos.push(g);
      const mat = new MeshStandardMaterial({
        vertexColors: true,
        roughness: sp.roughness,
        metalness: sp.metalness,
        emissive: new Color(sp.emissive ?? 0x000000),
      });
      const wind = { value: sp.wind };
      patchAerial(
        mat,
        aerialSteps,
        (shader) => {
          Object.assign(shader.uniforms, propUniforms, { uWind: wind });
          shader.vertexShader = shader.vertexShader
            .replace('#include <common>', '#include <common>\nuniform float uTime;\nuniform float uWind;')
            .replace(
              '#include <begin_vertex>',
              `#include <begin_vertex>
              if (uWind > 0.0) {
                #ifdef USE_INSTANCING
                  float wPhase = dot(instanceMatrix[3].xyz, vec3(0.071, 0.053, 0.037));
                #else
                  float wPhase = 0.0;
                #endif
                float hh = transformed.y * transformed.y;
                transformed.x += uWind * (sin(uTime * 1.3 + wPhase) * 0.6 + sin(uTime * 2.9 + wPhase * 1.7) * 0.4) * hh;
                transformed.z += uWind * 0.6 * cos(uTime * 1.1 + wPhase) * hh;
              }`,
            );
        },
        `prop:${sp.id}`,
      );
      this.materials.push(mat);
      const cap0 = sp.range <= sp.lod0 ? 4000 : sp.wind > 0 ? 1400 : 1600;
      const m0 = new InstancedMesh(g.lod0, mat, cap0);
      m0.instanceMatrix.setUsage(DynamicDrawUsage);
      m0.count = 0;
      m0.frustumCulled = false;
      m0.castShadow = sp.castShadow;
      m0.receiveShadow = true;
      this.group.add(m0);
      this.lod0.push(m0);
      if (g.lod1) {
        const m1 = new InstancedMesh(g.lod1, mat, 6000);
        m1.instanceMatrix.setUsage(DynamicDrawUsage);
        m1.count = 0;
        m1.frustumCulled = false;
        m1.castShadow = false;
        m1.receiveShadow = false;
        this.group.add(m1);
        this.lod1.push(m1);
      } else this.lod1.push(null);
    }
  }

  setQuality(density: number, rangeScale: number): void {
    if (density !== this.density || rangeScale !== this.rangeScale) {
      this.density = density;
      this.rangeScale = rangeScale;
      this.fillDirty = true;
      this.lastEnum.set(1e9, 0, 0);
    }
  }

  private maxRange(): number {
    let r = 0;
    for (const s of this.species) r = Math.max(r, s.range);
    return r * this.rangeScale;
  }

  /** Enumerate placement cells within range of the focus (handles cube-face crossings). */
  private enumerate(focus: Vector3): void {
    const n = _v.copy(focus).normalize();
    const dir: V3 = [n.x, n.y, n.z];
    const [t1, t2] = tangentBasis(dir);
    const R = this.def.radius;
    const range = this.maxRange() + this.cellSize;
    const step = this.cellSize * 0.5;
    const keys: { key: string; d: number }[] = [];
    const seen = new Set<string>();
    const N = Math.ceil(range / step);
    for (let j = -N; j <= N; j++) {
      for (let i = -N; i <= N; i++) {
        const dx = i * step;
        const dy = j * step;
        const d = Math.hypot(dx, dy);
        if (d > range) continue;
        const x = dir[0] + (dx * t1[0] + dy * t2[0]) / R;
        const y = dir[1] + (dx * t1[1] + dy * t2[1]) / R;
        const z = dir[2] + (dx * t1[2] + dy * t2[2]) / R;
        const f = dirToFace(x, y, z);
        const c = chunkAt(f.face, f.u, f.v, this.def.maxLevel);
        const key = chunkKey(f.face, this.def.maxLevel, c.x, c.y);
        if (seen.has(key)) continue;
        seen.add(key);
        keys.push({ key, d });
      }
    }
    keys.sort((a, b) => a.d - b.d);
    this.pending = keys.filter((k) => !this.cells.has(k.key)).map((k) => k.key);
    // Forget cells far outside the range.
    const keep = new Set(keys.map((k) => k.key));
    for (const k of this.cells.keys()) if (!keep.has(k)) this.cells.delete(k);
  }

  /** Clearings stay free of props; small decorative plants may approach closer. */
  private excluded(dx: number, dy: number, dz: number, decorative: boolean): boolean {
    const R = this.def.radius;
    for (let i = 0; i < this.exclusions.length; i++) {
      const e = this.exclusions[i];
      const ex = dx - e.dir[0], ey = dy - e.dir[1], ez = dz - e.dir[2];
      const r = decorative && i === 0 ? 18 : e.r;
      if (Math.sqrt(ex * ex + ey * ey + ez * ez) * R < r) return true;
    }
    return false;
  }

  /** Generate one placement cell (half-open ownership: candidates lie inside it). */
  private generateCell(key: string): void {
    const [face, level, x, y] = key.split('/').map(Number);
    const b = chunkBounds(level, x, y);
    const R = this.def.radius;
    const out: PropInstance[] = [];
    const d = [0, 0, 0];
    const gen = this.gen;
    const eps = 1.5 / R;
    for (let si = 0; si < this.species.length; si++) {
      const sp = this.species[si];
      for (let k = 0; k < sp.candidates; k++) {
        const h = hashCombine(this.def.seed, 'prop', face, x, y, si, k);
        const u = b.u0 + (b.u1 - b.u0) * hf(h, 1);
        const v = b.v0 + (b.v1 - b.v0) * hf(h, 2);
        faceDir(face, u, v, d);
        if (this.excluded(d[0], d[1], d[2], sp.collider === null)) continue;
        gen.info(d[0], d[1], d[2], this.info);
        // Slope from the continuous surface (finite differences).
        const [a1, a2] = tangentBasis([d[0], d[1], d[2]]);
        const h0 = this.info.height;
        const ha = gen.height(d[0] + eps * a1[0], d[1] + eps * a1[1], d[2] + eps * a1[2]);
        const hb = gen.height(d[0] + eps * a2[0], d[1] + eps * a2[1], d[2] + eps * a2[2]);
        const gx = (ha - h0) / 1.5;
        const gy = (hb - h0) / 1.5;
        const slope = 1 - 1 / Math.sqrt(1 + gx * gx + gy * gy);
        if (slope > sp.maxSlope) continue;
        if (hf(h, 3) >= sp.density(this.info, slope)) continue;
        const height = sp.hMin + (sp.hMax - sp.hMin) * hf(h, 4) ** 1.5;
        const r = R + h0 - height * sp.sink;
        const up = new Vector3(d[0], d[1], d[2]);
        if (sp.tiltToNormal > 0) {
          // Surface normal from the gradient, blended with radial up.
          const nrm = new Vector3(d[0], d[1], d[2])
            .addScaledVector(new Vector3(a1[0], a1[1], a1[2]), -gx)
            .addScaledVector(new Vector3(a2[0], a2[1], a2[2]), -gy)
            .normalize();
          up.lerp(nrm, sp.tiltToNormal).normalize();
        }
        out.push({
          id: `${this.def.id}:${sp.id}:${face}/${x}/${y}:${k}`,
          species: sp,
          p: new Vector3(d[0] * r, d[1] * r, d[2] * r),
          up,
          yaw: hf(h, 5) * Math.PI * 2,
          h: height,
          tint: hf(h, 6),
        });
      }
    }
    this.cells.set(key, out);
  }

  /**
   * Per-frame update. `focus` (controlled entity) and `view` (camera) are
   * relative to the body center; `planetLocal` is the body center in local coordinates.
   */
  update(dt: number, focus: Vector3, view: Vector3, planetLocal: Vector3, nearGround: boolean): void {
    propUniforms.uTime.value += dt;
    // Rendering (cells, ranges, LODs) follows the camera; colliders follow the controlled entity.
    if (view.distanceTo(this.lastEnum) > this.cellSize) {
      this.lastEnum.copy(view);
      this.enumerate(view);
    }
    // Generate pending cells within a small main-thread budget.
    const t0 = performance.now();
    let made = 0;
    while (this.pending.length > 0 && performance.now() - t0 < 1.5) {
      this.generateCell(this.pending.shift()!);
      made++;
    }
    this.stats.genMs = performance.now() - t0;
    this.stats.pending = this.pending.length;
    if (made > 0) this.fillDirty = true;
    this.fillTimer -= dt;
    if ((this.fillDirty && this.fillTimer <= 0) || view.distanceTo(this.lastFill) > 25) this.refill(view);
    this.group.position.copy(this.anchor).add(planetLocal);
    if (nearGround && focus.distanceTo(this.lastCol) > 8) {
      this.lastCol.copy(focus);
      this.updateColliders(focus, planetLocal);
    } else if (!nearGround && this.colliders.size > 0) {
      this.clearColliders();
    }
  }

  private refill(focus: Vector3): void {
    this.fillDirty = false;
    this.fillTimer = 0.4;
    this.lastFill.copy(focus);
    this.anchor.copy(focus);
    const lists0: { inst: PropInstance; d: number }[][] = this.species.map(() => []);
    const lists1: { inst: PropInstance; d: number }[][] = this.species.map(() => []);
    let total = 0;
    for (const insts of this.cells.values()) {
      for (const inst of insts) {
        total++;
        const sp = inst.species;
        const si = this.species.indexOf(sp);
        // Decorative density scaling (never affects mission objects).
        if (this.density < 1 && inst.tint > this.density) continue;
        const d = inst.p.distanceTo(focus);
        const range = sp.range * this.rangeScale;
        if (d > range) continue;
        if (d < sp.lod0 * this.rangeScale || !this.lod1[si]) lists0[si].push({ inst, d });
        else lists1[si].push({ inst, d });
      }
    }
    let drawn = 0;
    for (let si = 0; si < this.species.length; si++) {
      drawn += this.fillMesh(this.lod0[si], lists0[si]);
      const m1 = this.lod1[si];
      if (m1) drawn += this.fillMesh(m1, lists1[si]);
    }
    this.stats.cells = this.cells.size;
    this.stats.instances = total;
    this.stats.drawn = drawn;
  }

  private fillMesh(mesh: InstancedMesh, list: { inst: PropInstance; d: number }[]): number {
    const cap = mesh.instanceMatrix.count;
    if (list.length > cap) {
      list.sort((a, b) => a.d - b.d);
      list.length = cap;
    }
    for (let i = 0; i < list.length; i++) {
      const inst = list[i].inst;
      _q.setFromUnitVectors(_Y, inst.up);
      _qy.setFromAxisAngle(_Y, inst.yaw);
      _q.multiply(_qy);
      _v.copy(inst.p).sub(this.anchor);
      _s.setScalar(inst.h);
      _m.compose(_v, _q, _s);
      mesh.setMatrixAt(i, _m);
      const t = 0.88 + inst.tint * 0.24;
      _c.setRGB(t, t * (0.97 + inst.tint * 0.05), t * (0.95 + (1 - inst.tint) * 0.08));
      mesh.setColorAt(i, _c);
    }
    mesh.count = list.length;
    mesh.instanceMatrix.needsUpdate = true;
    if (mesh.instanceColor) mesh.instanceColor.needsUpdate = true;
    return list.length;
  }

  /** Simple colliders for nearby major props (rocks, trunks). */
  private updateColliders(focus: Vector3, planetLocal: Vector3): void {
    const want: PropInstance[] = [];
    for (const insts of this.cells.values()) {
      for (const inst of insts) {
        if (!inst.species.collider) continue;
        const d = inst.p.distanceTo(focus);
        if (d < 80) want.push(inst);
      }
    }
    want.sort((a, b) => a.p.distanceTo(focus) - b.p.distanceTo(focus));
    want.length = Math.min(want.length, BUDGETS.maxPropColliders);
    const keep = new Set(want.map((w) => w.id));
    let changed = false;
    for (const [id, body] of this.colliders) {
      if (!keep.has(id)) {
        this.physics.world.removeRigidBody(body);
        this.colliders.delete(id);
        changed = true;
      }
    }
    for (const inst of want) {
      if (this.colliders.has(inst.id)) continue;
      const c = inst.species.collider!;
      _q.setFromUnitVectors(_Y, inst.up);
      const center = _v.copy(inst.up).multiplyScalar(c.y * inst.h).add(inst.p).add(planetLocal);
      const body = this.physics.world.createRigidBody(
        RAPIER.RigidBodyDesc.fixed().setTranslation(center.x, center.y, center.z).setRotation({ x: _q.x, y: _q.y, z: _q.z, w: _q.w }),
      );
      const desc =
        c.type === 'capsule'
          ? RAPIER.ColliderDesc.capsule(c.halfHeight * inst.h, c.radius * inst.h)
          : RAPIER.ColliderDesc.ball(c.radius * inst.h);
      desc.setCollisionGroups(GROUPS.props).setSolverGroups(GROUPS.props).setFriction(0.8);
      this.physics.world.createCollider(desc, body);
      this.colliders.set(inst.id, body);
      changed = true;
    }
    this.stats.colliders = this.colliders.size;
    if (changed) this.physics.refreshQueries();
  }

  private clearColliders(): void {
    for (const body of this.colliders.values()) this.physics.world.removeRigidBody(body);
    this.colliders.clear();
    this.stats.colliders = 0;
    this.physics.refreshQueries();
  }

  /** Instances near a planet-relative point (for scanning and interaction). */
  nearby(focus: Vector3, radius: number, out: PropInstance[] = []): PropInstance[] {
    out.length = 0;
    for (const insts of this.cells.values()) {
      for (const inst of insts) if (inst.p.distanceTo(focus) < radius) out.push(inst);
    }
    return out;
  }

  get triangleEstimate(): number {
    let t = 0;
    for (let si = 0; si < this.species.length; si++) {
      const g0 = this.geos[si].lod0;
      t += (g0.attributes.position.count / 3) * this.lod0[si].count;
      const g1 = this.geos[si].lod1;
      const m1 = this.lod1[si];
      if (g1 && m1) t += (g1.attributes.position.count / 3) * m1.count;
    }
    return t;
  }

  dispose(): void {
    this.clearColliders();
    for (const g of this.geos) {
      g.lod0.dispose();
      g.lod1?.dispose();
    }
    for (const m of this.materials) m.dispose();
    for (const m of this.lod0) m.dispose();
    for (const m of this.lod1) m?.dispose();
    this.group.removeFromParent();
  }
}
