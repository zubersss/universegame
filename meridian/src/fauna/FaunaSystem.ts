import {
  DynamicDrawUsage,
  Group,
  InstancedBufferAttribute,
  InstancedMesh,
  Matrix4,
  MeshStandardMaterial,
  Vector3,
  Vector4,
} from 'three';
import type { BodyDef } from '../world/bodies';
import type { SurfaceGenerator } from '../world/surface';
import { chunkAt, chunkKey, dirToFace } from '../world/cube';
import { levelSpacing } from '../terrain/chunkGen';
import { tangentBasis, type MissionSites, type V3 } from '../world/sites';
import { mulberry32 } from '../core/rng';
import { patchAerial } from '../render/Atmosphere';
import { newCreatureState, stepBehaviour, type CreatureState, type FaunaEvent, type Threats } from './behaviour';
import { faunaFor, type FaunaSpecies } from './faunaSpecies';
import { offsetDir, spawnCell, spawnLevel, type Spawn } from './spawn';
import type { FaunaGeometry } from './faunaMeshes';

/** What the creatures react to this frame (all planet-relative, double precision). */
export interface FaunaContext {
  /** Camera position: drives LOD, update rates and culling. */
  view: Vector3;
  /** Body center in local render coordinates. */
  planetLocal: Vector3;
  /** Player position when on foot, else null. */
  player: Vector3 | null;
  ship: Vector3;
  /** The ship is flying low or thrusting near the ground (engine noise, downwash). */
  shipLoud: boolean;
}

export class Creature {
  readonly state: CreatureState;
  readonly rnd: () => number;
  /** Feet position relative to the body center (double). */
  readonly p = new Vector3();
  readonly up = new Vector3(0, 1, 0);
  /** Gait phase (rad). */
  phase = 0;
  /** Unsimulated time for coarse update rates (s). */
  acc = 0;
  /** Distance to the camera at the last frame (m). */
  dist = Infinity;
  /** Footfall index within the gait cycle at the last 'step' event (0 = first beat). */
  beat = 0;
  constructor(readonly spawn: Spawn) {
    this.state = newCreatureState(spawn.x, spawn.z, spawn.yaw, (spawn.seed % 1000) / 200);
    this.rnd = mulberry32(spawn.seed);
  }
  get id(): string {
    return this.spawn.id;
  }
  get species(): FaunaSpecies {
    return this.spawn.species;
  }
  get h(): number {
    return this.spawn.h;
  }
}

/** Distance bands (m): full-rate updates, quarter rate, coarse, frozen beyond range. */
export const FAUNA_RATES = { near: 70, mid: 200, midEvery: 4, farEvery: 15, maxStep: 0.1, maxAcc: 2 } as const;

/** Instance caps per species and LOD (bounded draw cost whatever the herd density). */
const CAP0 = 48;
const CAP1 = 160;

/** Shared clock for appendage sway. */
const faunaUniforms = { uTime: { value: 0 } };

const _m = new Matrix4();
const _x = new Vector3();
const _f = new Vector3();
const _v = new Vector3();
const _s = new Vector3();
const _dir: number[] = [0, 0, 0];
const _threats: Threats = { player: false, px: 0, pz: 0, ship: false, sx: 0, sz: 0 };

function commit(mesh: InstancedMesh, anim: InstancedBufferAttribute, n: number): number {
  mesh.count = n;
  mesh.instanceMatrix.needsUpdate = true;
  anim.needsUpdate = true;
  return n;
}

const GAIT_GLSL = /* glsl */ `
  {
    float fPh = aAnim.x;
    float fAmp = aAnim.y;
    float fBob = fAmp * uGait.w * sin(fPh * 3.0);
    if (aLeg.x > -0.5) {
      // Legs: the foot (t = 1) lifts and swings, the hip (t = 0) rides the body.
      float lp = fPh + aLeg.x * uGait.x;
      float lt = aLeg.y;
      transformed.y += max(0.0, sin(lp)) * fAmp * uGait.y * lt + fBob * (1.0 - lt);
      transformed.z += cos(lp) * fAmp * uGait.z * lt;
    } else {
      transformed.y += fBob;
      if (aLeg.x < -1.5) {
        // Vanes: a slow sway, stronger at the tips.
        float tip = clamp((transformed.y - 0.83) * 6.0, 0.0, 1.0);
        transformed.x += sin(uTime * 1.2 + fPh * 0.05 + transformed.z * 7.0) * 0.018 * aAnim.z * tip;
      }
    }
  }
`;

/**
 * Creatures of the active body: deterministic herds per spawn cell, a small
 * behaviour state machine per creature, ground snapping on the analytic
 * surface, two instanced LODs per species and procedural vertex animation.
 * Separate from PropSystem (creatures move; the prop fingerprint must not).
 */
export class FaunaSystem {
  readonly group = new Group();
  private readonly species: FaunaSpecies[];
  private readonly geos: FaunaGeometry[] = [];
  private readonly materials: MeshStandardMaterial[] = [];
  private readonly lod0: InstancedMesh[] = [];
  private readonly lod1: InstancedMesh[] = [];
  private readonly anim0: InstancedBufferAttribute[] = [];
  private readonly anim1: InstancedBufferAttribute[] = [];
  private readonly cells = new Map<string, Creature[]>();
  private pending: string[] = [];
  private readonly lastEnum = new Vector3(1e9, 0, 0);
  private readonly anchor = new Vector3();
  private readonly level: number;
  private readonly cellSize: number;
  private frame = 0;
  private readonly counts0: Int32Array;
  private readonly counts1: Int32Array;
  rangeScale = 1;
  /** Fauna events for sound (ECHO) and effects (LUMEN); null when unused. */
  onEvent: ((ev: FaunaEvent, c: Creature) => void) | null = null;
  readonly stats = { cells: 0, creatures: 0, drawn: 0, updated: 0, genMs: 0, pending: 0 };

  constructor(
    readonly def: BodyDef,
    private readonly gen: SurfaceGenerator,
    private readonly sites: MissionSites,
    aerialSteps: number,
  ) {
    this.group.name = `fauna-${def.id}`;
    this.species = faunaFor(def.id);
    this.level = spawnLevel(def);
    this.cellSize = levelSpacing(def, this.level) * 32;
    this.counts0 = new Int32Array(this.species.length);
    this.counts1 = new Int32Array(this.species.length);
    for (const sp of this.species) {
      const g = sp.make();
      this.geos.push(g);
      const mat = new MeshStandardMaterial({ vertexColors: true, roughness: sp.roughness, metalness: 0 });
      const gait = { value: new Vector4(sp.gait.legStep, sp.gait.lift, sp.gait.swing, sp.gait.bob) };
      patchAerial(
        mat,
        aerialSteps,
        (shader) => {
          Object.assign(shader.uniforms, faunaUniforms, { uGait: gait });
          shader.vertexShader = shader.vertexShader
            .replace('#include <common>', '#include <common>\nuniform float uTime;\nuniform vec4 uGait;\nattribute vec2 aLeg;\nattribute vec3 aAnim;')
            .replace('#include <begin_vertex>', `#include <begin_vertex>\n${GAIT_GLSL}`);
        },
        'fauna',
      );
      this.materials.push(mat);
      const mk = (geo: typeof g.lod0, cap: number, shadow: boolean, anims: InstancedBufferAttribute[], list: InstancedMesh[]) => {
        const a = new InstancedBufferAttribute(new Float32Array(cap * 3), 3);
        a.setUsage(DynamicDrawUsage);
        geo.setAttribute('aAnim', a);
        const m = new InstancedMesh(geo, mat, cap);
        m.instanceMatrix.setUsage(DynamicDrawUsage);
        m.count = 0;
        m.frustumCulled = false;
        m.castShadow = shadow;
        m.receiveShadow = true;
        this.group.add(m);
        anims.push(a);
        list.push(m);
      };
      mk(g.lod0, CAP0, true, this.anim0, this.lod0);
      mk(g.lod1, CAP1, false, this.anim1, this.lod1);
    }
  }

  setQuality(rangeScale: number): void {
    if (rangeScale !== this.rangeScale) {
      this.rangeScale = rangeScale;
      this.lastEnum.set(1e9, 0, 0);
    }
  }

  private maxRange(): number {
    let r = 0;
    for (const s of this.species) r = Math.max(r, s.range);
    return r * this.rangeScale;
  }

  /** Spawn cells within range of the camera (handles cube-face crossings). */
  private enumerate(view: Vector3): void {
    const n = _v.copy(view).normalize();
    const dir: V3 = [n.x, n.y, n.z];
    const [t1, t2] = tangentBasis(dir);
    const R = this.def.radius;
    const range = this.maxRange() + this.cellSize * 0.75;
    const step = this.cellSize * 0.5;
    const want = new Map<string, number>();
    const N = Math.ceil(range / step);
    for (let j = -N; j <= N; j++) {
      for (let i = -N; i <= N; i++) {
        const dx = i * step;
        const dy = j * step;
        const d = Math.hypot(dx, dy);
        if (d > range) continue;
        const f = dirToFace(dir[0] + (dx * t1[0] + dy * t2[0]) / R, dir[1] + (dx * t1[1] + dy * t2[1]) / R, dir[2] + (dx * t1[2] + dy * t2[2]) / R);
        const c = chunkAt(f.face, f.u, f.v, this.level);
        const key = chunkKey(f.face, this.level, c.x, c.y);
        const prev = want.get(key);
        if (prev === undefined || d < prev) want.set(key, d);
      }
    }
    this.pending = [...want.entries()].filter(([k]) => !this.cells.has(k)).sort((a, b) => a[1] - b[1]).map(([k]) => k);
    // Forget cells (and their creatures' runtime state) once well out of range.
    for (const k of this.cells.keys()) if (!want.has(k)) this.cells.delete(k);
  }

  private generate(key: string): void {
    const [face, , x, y] = key.split('/').map(Number);
    const spawns = spawnCell(this.def, this.gen, this.sites, this.species, face, x, y);
    const list = spawns.map((s) => new Creature(s));
    for (const c of list) this.place(c);
    this.cells.set(key, list);
  }

  /**
   * Snap a creature to the surface at its current tangent offset. `gen` must be
   * the body's clearing-aware surface (the one terrain and colliders use).
   */
  place(c: Creature): void {
    const s = c.spawn;
    offsetDir(s.home, s.t1, s.t2, c.state.x, c.state.z, this.def.radius, _dir);
    const r = this.def.radius + this.gen.height(_dir[0], _dir[1], _dir[2]) - 0.03 * c.h;
    c.up.set(_dir[0], _dir[1], _dir[2]);
    c.p.set(_dir[0] * r, _dir[1] * r, _dir[2] * r);
  }

  /** Behaviour + gait + ground snap for one creature over dt seconds. */
  private simulate(c: Creature, dt: number, ctx: FaunaContext): void {
    const s = c.spawn;
    const sp = s.species;
    const R = this.def.radius;
    const hx = s.home[0] * R, hy = s.home[1] * R, hz = s.home[2] * R;
    // Threats projected into the home tangent frame (ignored when far or around the curve).
    const t = _threats;
    t.player = false;
    t.ship = false;
    if (ctx.player) {
      const dx = ctx.player.x - hx, dy = ctx.player.y - hy, dz = ctx.player.z - hz;
      if (dx * dx + dy * dy + dz * dz < 1e6) {
        t.player = true;
        t.px = dx * s.t1[0] + dy * s.t1[1] + dz * s.t1[2];
        t.pz = dx * s.t2[0] + dy * s.t2[1] + dz * s.t2[2];
      }
    }
    if (ctx.shipLoud) {
      const dx = ctx.ship.x - hx, dy = ctx.ship.y - hy, dz = ctx.ship.z - hz;
      if (dx * dx + dy * dy + dz * dz < 1e6) {
        t.ship = true;
        t.sx = dx * s.t1[0] + dy * s.t1[1] + dz * s.t1[2];
        t.sz = dx * s.t2[0] + dy * s.t2[1] + dz * s.t2[2];
      }
    }
    const strideLen = sp.stride * c.h;
    while (dt > 0) {
      const h = Math.min(dt, FAUNA_RATES.maxStep);
      dt -= h;
      const ev = stepBehaviour(c.state, sp.behaviour, t, h, c.rnd);
      const before = Math.floor(c.phase / sp.gait.legStep);
      c.phase += (c.state.speed * h * Math.PI * 2) / strideLen;
      if (c.phase > 1e4) c.phase -= Math.PI * 2 * 1000;
      const after = Math.floor(c.phase / sp.gait.legStep);
      if (this.onEvent) {
        if (ev) this.onEvent(ev, c);
        if (after !== before && c.dist < FAUNA_RATES.near) {
          c.beat = after % Math.round((Math.PI * 2) / sp.gait.legStep);
          this.onEvent('step', c);
        }
      }
    }
    this.place(c);
  }

  update(dt: number, ctx: FaunaContext): void {
    faunaUniforms.uTime.value += dt;
    this.frame++;
    if (ctx.view.distanceTo(this.lastEnum) > this.cellSize * 0.25) {
      this.lastEnum.copy(ctx.view);
      this.enumerate(ctx.view);
    }
    const t0 = performance.now();
    while (this.pending.length > 0 && performance.now() - t0 < 1) this.generate(this.pending.shift()!);
    this.stats.genMs = performance.now() - t0;
    this.stats.pending = this.pending.length;

    const range = this.maxRange();
    let updated = 0;
    let total = 0;
    for (const list of this.cells.values()) {
      for (let i = 0; i < list.length; i++) {
        const c = list[i];
        total++;
        c.dist = c.p.distanceTo(ctx.view);
        if (c.dist > range) {
          c.acc = 0; // frozen out of range
          continue;
        }
        c.acc = Math.min(FAUNA_RATES.maxAcc, c.acc + dt);
        const every = c.dist < FAUNA_RATES.near ? 1 : c.dist < FAUNA_RATES.mid ? FAUNA_RATES.midEvery : FAUNA_RATES.farEvery;
        if (every > 1 && (this.frame + (c.spawn.seed & 0xff)) % every !== 0) continue;
        this.simulate(c, c.acc, ctx);
        c.acc = 0;
        updated++;
      }
    }
    this.stats.updated = updated;
    this.stats.creatures = total;
    this.stats.cells = this.cells.size;
    this.fill(ctx);
  }

  /** Write instance matrices and animation attributes for visible creatures. */
  private fill(ctx: FaunaContext): void {
    this.anchor.copy(ctx.view);
    this.group.position.copy(this.anchor).add(ctx.planetLocal);
    const counts0 = this.counts0.fill(0);
    const counts1 = this.counts1.fill(0);
    for (const list of this.cells.values()) {
      for (const c of list) {
        const sp = c.species;
        if (c.dist > sp.range * this.rangeScale) continue;
        const si = this.species.indexOf(sp);
        const near = c.dist < sp.lod0 * this.rangeScale;
        const mesh = near ? this.lod0[si] : this.lod1[si];
        const anim = near ? this.anim0[si] : this.anim1[si];
        const counts = near ? counts0 : counts1;
        const i = counts[si];
        if (i >= mesh.instanceMatrix.count) continue;
        counts[si]++;
        // Basis: radial up, heading from the home frame (re-orthogonalized here).
        const s = c.spawn;
        const st = c.state;
        const sy = Math.sin(st.yaw), cy = Math.cos(st.yaw);
        _f.set(s.t2[0] * cy + s.t1[0] * sy, s.t2[1] * cy + s.t1[1] * sy, s.t2[2] * cy + s.t1[2] * sy);
        _f.addScaledVector(c.up, -_f.dot(c.up)).normalize();
        _x.crossVectors(c.up, _f);
        _m.makeBasis(_x, c.up, _f);
        _s.setScalar(c.h);
        _m.scale(_s);
        _v.copy(c.p).sub(this.anchor);
        _m.setPosition(_v);
        mesh.setMatrixAt(i, _m);
        const walk = Math.min(1.3, st.speed / sp.behaviour.walkSpeed);
        anim.setXYZ(i, c.phase, walk, st.mode === 'alert' ? 0.3 : 1);
      }
    }
    let drawn = 0;
    for (let si = 0; si < this.species.length; si++) {
      drawn += commit(this.lod0[si], this.anim0[si], counts0[si]) + commit(this.lod1[si], this.anim1[si], counts1[si]);
    }
    this.stats.drawn = drawn;
  }

  /** Creatures near a planet-relative point (scanning, tests). */
  nearby(focus: Vector3, radius: number, out: Creature[] = []): Creature[] {
    out.length = 0;
    for (const list of this.cells.values()) {
      for (const c of list) if (c.p.distanceTo(focus) < radius) out.push(c);
    }
    return out;
  }

  get triangleEstimate(): number {
    let t = 0;
    for (let si = 0; si < this.species.length; si++) {
      t += (this.geos[si].lod0.attributes.position.count / 3) * this.lod0[si].count;
      t += (this.geos[si].lod1.attributes.position.count / 3) * this.lod1[si].count;
    }
    return t;
  }

  dispose(): void {
    for (const g of this.geos) {
      g.lod0.dispose();
      g.lod1.dispose();
    }
    for (const m of this.materials) m.dispose();
    for (const m of this.lod0) m.dispose();
    for (const m of this.lod1) m.dispose();
    this.cells.clear();
    this.group.removeFromParent();
  }
}

/**
 * Loudness (0..1) of a fauna sound event for the audio mixer: alarms full,
 * calls softer, footfalls scaled by gait speed with the first beat of each
 * cycle accented so the species' rhythm is audible.
 */
export function faunaSoundIntensity(ev: FaunaEvent, c: Creature): number {
  if (ev === 'alarm') return 1;
  if (ev === 'call') return 0.6;
  const pace = Math.min(1, 0.4 + c.state.speed / c.species.behaviour.fleeSpeed);
  return (c.beat === 0 ? 1 : 0.6) * pace;
}
