import {
  BufferAttribute,
  BufferGeometry,
  Frustum,
  Group,
  Mesh,
  Sphere,
  Vector3,
  type Material,
  type MeshStandardMaterial,
} from 'three';
import type { BodyDef } from '../world/bodies';
import { chunkBounds, chunkKey, dirToFace, faceCubePoint, faceDir } from '../world/cube';
import { GRID_VERTS, levelSpacing, makeChunkIndex, type ChunkData } from './chunkGen';
import type { ChunkRequest, ChunkStore } from './ChunkStore';
import { MORPH_LEVELS } from './terrainMaterial';

const MORPH_TIME = 0.2;

export class TNode {
  readonly key: string;
  children: TNode[] | null = null;
  mesh: Mesh | null = null;
  data: ChunkData | null = null;
  /** 0 = own shape, 1 = parent's shape. */
  morph = 0;
  morphVel = 0;
  merging = false;
  forceSplitAt = -1;
  constructor(
    readonly face: number,
    readonly level: number,
    readonly x: number,
    readonly y: number,
    readonly parent: TNode | null,
  ) {
    this.key = chunkKey(face, level, x, y);
  }
  get isLeaf(): boolean {
    return this.children === null;
  }
}

export interface TerrainView {
  /** Camera position relative to the planet center (double). */
  camPlanet: Vector3;
  /** Frustum in local coordinates. */
  frustum: Frustum;
  /** Planet center in local coordinates. */
  planetLocal: Vector3;
  fovY: number;
  viewportH: number;
  /** Controlled entity relative to the planet center (forced contact detail). */
  focusPlanet: Vector3;
  contactRadius: number;
}

export interface TerrainStats {
  leaves: number;
  rendered: number;
  morphing: number;
  triangles: number;
  maxLevel: number;
  splitsBlockedByBudget: number;
  horizonCulled: number;
}

const _s = new Sphere();
const _c = new Vector3();
const dirTmp = [0, 0, 0];

/** Conservative horizon test: is a bounding sphere entirely behind the planet's occluding sphere? */
export function horizonCulled(cx: number, cy: number, cz: number, r: number, e: Vector3, occluderR: number): boolean {
  const D = e.length();
  if (D <= occluderR) return false;
  const th = Math.sqrt(D * D - occluderR * occluderR);
  const lx = cx - e.x, ly = cy - e.y, lz = cz - e.z;
  const L = Math.sqrt(lx * lx + ly * ly + lz * lz);
  if (L - r <= th) return false;
  const alpha = Math.asin(occluderR / D);
  const cosT = (lx * -e.x + ly * -e.y + lz * -e.z) / (L * D);
  const theta = Math.acos(Math.max(-1, Math.min(1, cosT)));
  return theta + Math.asin(Math.min(1, r / L)) < alpha;
}

export class TerrainManager {
  readonly root = new Group();
  readonly roots: TNode[] = [];
  private readonly index: BufferAttribute;
  private frame = 0;
  private readonly morphing = new Set<TNode>();
  private readonly meshNodes = new Set<TNode>();
  private demand: ChunkRequest[] = [];
  splitPx = 4;
  maxChunks = 160;
  horizonCulling = true;
  /** Max new chunk meshes per update (upload budget). */
  meshBudget = 8;
  private meshBudgetLeft = 0;
  private renderedLeaves = 0;
  readonly stats: TerrainStats = { leaves: 0, rendered: 0, morphing: 0, triangles: 0, maxLevel: 0, splitsBlockedByBudget: 0, horizonCulled: 0 };
  private readonly kErr: number;
  private view: TerrainView | null = null;
  /** Keys whose meshes must be unmorphed (collision-backed contact tiles). */
  contactKeys: Set<string> = new Set();
  /**
   * Handoff control: while true no node splits and every node merges back
   * toward the level-0 roots (the mesh the body's distant proxy shows).
   */
  holdCoarse = false;
  /** Material for liquid surfaces (chunks with water data get a child mesh); null = no water drawn. */
  waterMaterial: Material | null = null;

  constructor(
    readonly def: BodyDef,
    readonly store: ChunkStore,
    private readonly materials: MeshStandardMaterial[],
  ) {
    this.root.name = `terrain-${def.id}`;
    this.index = new BufferAttribute(makeChunkIndex(), 1);
    this.kErr = def.id === 'cairn' ? 0.1 : 0.13;
    for (let f = 0; f < 6; f++) this.roots.push(new TNode(f, 0, 0, 0, null));
  }

  /** True once the complete six-face coarse planet is renderable (every root meshed or split). */
  get coarseReady(): boolean {
    return this.roots.every((r) => r.mesh !== null || !r.isLeaf);
  }

  /** True when only the level-0 roots are rendered (matches the proxy exactly). */
  get atRoots(): boolean {
    return this.morphing.size === 0 && this.roots.every((r) => r.isLeaf && r.mesh !== null);
  }

  // ------------------------------------------------------------- geometry

  private nodeSphere(n: TNode, out: Sphere): Sphere {
    const d = n.data ?? this.store.get(n.key) ?? null;
    if (d) {
      out.center.set(d.center[0] + d.bounds[0], d.center[1] + d.bounds[1], d.center[2] + d.bounds[2]);
      out.radius = d.bounds[3];
      return out;
    }
    const b = chunkBounds(n.level, n.x, n.y);
    faceDir(n.face, (b.u0 + b.u1) / 2, (b.v0 + b.v1) / 2, dirTmp);
    const R = this.def.radius;
    const mid = R + this.def.maxHeight * 0.5;
    out.center.set(dirTmp[0] * mid, dirTmp[1] * mid, dirTmp[2] * mid);
    out.radius = ((Math.PI / 2) * R) / 2 ** n.level * 0.75 + this.def.maxHeight;
    return out;
  }

  private errorMeters(n: TNode): number {
    const h = this.kErr * levelSpacing(this.def, n.level);
    const d = n.data;
    if (!d || n.level < 2) return h;
    return Math.max(0.6 * d.ownError, 0.3 * h);
  }

  private projectedError(n: TNode): number {
    const v = this.view!;
    this.nodeSphere(n, _s);
    const dist = Math.max(1, _s.center.distanceTo(v.camPlanet) - _s.radius);
    return (this.errorMeters(n) * v.viewportH) / (2 * dist * Math.tan(v.fovY / 2));
  }

  private inContact(n: TNode): boolean {
    const v = this.view!;
    this.nodeSphere(n, _s);
    return _s.center.distanceTo(v.focusPlanet) < _s.radius + v.contactRadius;
  }

  private visible(n: TNode): boolean {
    const v = this.view!;
    this.nodeSphere(n, _s);
    if (this.horizonCulling && horizonCulled(_s.center.x, _s.center.y, _s.center.z, _s.radius, v.camPlanet, this.def.radius * 0.999)) {
      return false;
    }
    _s.center.add(v.planetLocal);
    return v.frustum.intersectsSphere(_s);
  }

  // ------------------------------------------------------------ balance

  private leafAt(face: number, u: number, v: number): TNode {
    let n = this.roots[face];
    while (n.children) {
      const b = chunkBounds(n.level, n.x, n.y);
      const cu = u >= (b.u0 + b.u1) / 2 ? 1 : 0;
      const cv = v >= (b.v0 + b.v1) / 2 ? 1 : 0;
      n = n.children[cv * 2 + cu];
    }
    return n;
  }

  /** Points just outside each edge of a node (perEdge per edge), resolved across faces. */
  private neighborLeaves(n: TNode, perEdge: number, out: TNode[]): TNode[] {
    out.length = 0;
    const b = chunkBounds(n.level, n.x, n.y);
    const eps = 1e-7;
    for (let k = 0; k < perEdge; k++) {
      const t = (k + 0.5) / perEdge;
      const pts: [number, number][] = [
        [b.u0 - eps, b.v0 + (b.v1 - b.v0) * t],
        [b.u1 + eps, b.v0 + (b.v1 - b.v0) * t],
        [b.u0 + (b.u1 - b.u0) * t, b.v0 - eps],
        [b.u0 + (b.u1 - b.u0) * t, b.v1 + eps],
      ];
      for (const [u, v] of pts) {
        if (u >= -1 && u <= 1 && v >= -1 && v <= 1) out.push(this.leafAt(n.face, u, v));
        else {
          const p = faceCubePoint(n.face, u, v);
          const f = dirToFace(p[0], p[1], p[2]);
          out.push(this.leafAt(f.face, f.u, f.v));
        }
      }
    }
    return out;
  }

  private readonly nb: TNode[] = [];

  /** A leaf may split only if no neighbor is coarser; coarser neighbors are asked to split first. */
  private balanceAllowsSplit(n: TNode): boolean {
    let ok = true;
    for (const m of this.neighborLeaves(n, 2, this.nb)) {
      if (m.level < n.level) {
        m.forceSplitAt = this.frame;
        ok = false;
      }
    }
    return ok;
  }

  /** A node may merge only if no neighbor leaf is more than one level finer than it. */
  private balanceAllowsMerge(n: TNode): boolean {
    for (const m of this.neighborLeaves(n, 4, this.nb)) if (m.level > n.level + 1) return false;
    return true;
  }

  // -------------------------------------------------------------- meshes

  private ensureMesh(n: TNode): boolean {
    if (n.mesh) return true;
    const d = n.data ?? this.store.get(n.key) ?? null;
    if (!d) return false;
    if (this.meshBudgetLeft <= 0) return false;
    this.meshBudgetLeft--;
    n.data = d;
    const g = new BufferGeometry();
    g.setAttribute('position', new BufferAttribute(d.positions, 3));
    g.setAttribute('normal', new BufferAttribute(d.normals, 3));
    g.setAttribute('morphDelta', new BufferAttribute(d.morphDelta, 3));
    g.setAttribute('morphNormal', new BufferAttribute(d.morphNormal, 4, true));
    g.setAttribute('tileCoord', new BufferAttribute(d.tile, 3));
    g.setAttribute('surf', new BufferAttribute(d.attrs, 4, true));
    g.setIndex(this.index);
    g.boundingSphere = new Sphere(new Vector3(d.bounds[0], d.bounds[1], d.bounds[2]), d.bounds[3]);
    const m = new Mesh(g, this.materials[this.morphIndex(n.morph)]);
    m.position.set(d.center[0], d.center[1], d.center[2]);
    m.matrixAutoUpdate = false;
    m.updateMatrix();
    m.receiveShadow = true;
    m.castShadow = n.level >= this.def.maxLevel - 3;
    m.name = n.key;
    if (d.water && d.water.index.length > 0 && this.waterMaterial) {
      // Liquid surface as a child: same transform, visibility and lifetime as its chunk.
      const wg = new BufferGeometry();
      wg.setAttribute('position', new BufferAttribute(d.water.positions, 3));
      wg.setAttribute('normal', new BufferAttribute(d.water.normals, 3));
      wg.setAttribute('depth', new BufferAttribute(d.water.depth, 1));
      wg.setAttribute('tileCoord', new BufferAttribute(d.tile.subarray(0, GRID_VERTS * 3), 3));
      wg.setIndex(new BufferAttribute(d.water.index, 1));
      wg.boundingSphere = g.boundingSphere.clone();
      const wm = new Mesh(wg, this.waterMaterial);
      wm.matrixAutoUpdate = false;
      wm.renderOrder = 1;
      wm.receiveShadow = true;
      wm.name = `${n.key}:water`;
      m.add(wm);
    }
    this.root.add(m);
    n.mesh = m;
    this.meshNodes.add(n);
    return true;
  }

  private disposeMesh(n: TNode): void {
    if (!n.mesh) return;
    this.root.remove(n.mesh);
    for (const c of n.mesh.children) (c as Mesh).geometry.dispose();
    const g = n.mesh.geometry;
    g.setIndex(null); // keep the shared index buffer alive
    g.dispose();
    n.mesh = null;
    this.meshNodes.delete(n);
    this.morphing.delete(n);
  }

  private morphIndex(m: number): number {
    return Math.max(0, Math.min(MORPH_LEVELS, Math.round(m * MORPH_LEVELS)));
  }

  // ---------------------------------------------------------------- update

  private request(n: TNode, priority: number): void {
    this.demand.push({ key: n.key, bodyId: this.def.id, face: n.face, level: n.level, x: n.x, y: n.y, priority });
  }

  /** Extra demand from the collision system (contact tiles at max level). */
  extraDemand: ChunkRequest[] = [];

  update(view: TerrainView): void {
    this.view = view;
    this.frame++;
    this.demand = [];
    this.meshBudgetLeft = this.meshBudget;
    this.stats.splitsBlockedByBudget = 0;
    this.stats.horizonCulled = 0;
    this.renderedLeaves = this.meshNodes.size;
    for (const r of this.roots) {
      if (r.data || this.store.has(r.key)) this.visit(r);
      else this.request(r, 0);
    }
    for (const r of this.extraDemand) this.demand.push(r);
    this.store.setDemand(this.demand);
    this.updatePinned();
    this.updateStats();
  }

  private visit(n: TNode): void {
    if (n.isLeaf) {
      this.ensureMesh(n);
      if (n.level >= this.def.maxLevel || !n.mesh) return;
      if (!this.wantsSplit(n)) return;
      if (!this.balanceAllowsSplit(n)) return;
      // Request all four children; split only when all are ready.
      let ready = 0;
      const lvl = n.level + 1;
      const dist = this.nodeSphere(n, _s).center.distanceTo(this.view!.camPlanet);
      for (let cy = 0; cy < 2; cy++) {
        for (let cx = 0; cx < 2; cx++) {
          const key = chunkKey(n.face, lvl, n.x * 2 + cx, n.y * 2 + cy);
          if (this.store.has(key)) ready++;
          else
            this.demand.push({
              key, bodyId: this.def.id, face: n.face, level: lvl, x: n.x * 2 + cx, y: n.y * 2 + cy,
              priority: (this.inContact(n) ? 1e6 : 2e6) + dist,
            });
        }
      }
      if (ready === 4 && this.meshBudgetLeft >= 4) this.split(n);
      return;
    }
    // Split node.
    const kids = n.children!;
    const allLeaves = kids.every((c) => c.isLeaf);
    if (allLeaves) {
      const want = this.wantsMerge(n);
      if (want && !n.merging && this.balanceAllowsMerge(n)) {
        if (n.data || this.store.has(n.key)) {
          n.merging = true;
          for (const c of kids) {
            c.morphVel = 1;
            this.morphing.add(c);
          }
        } else {
          this.request(n, 3e6);
        }
      } else if (!want && n.merging) {
        n.merging = false;
        for (const c of kids) {
          c.morphVel = -1;
          this.morphing.add(c);
        }
      }
    }
    if (!n.merging) for (const c of kids) this.visit(c);
    else for (const c of kids) this.ensureMesh(c);
  }

  private wantsSplit(n: TNode): boolean {
    if (n.level >= this.def.maxLevel) return false;
    if (this.inContact(n)) return true;
    if (this.holdCoarse) return false;
    if (n.forceSplitAt >= this.frame - 1) return true;
    if (this.renderedLeaves + 3 > this.maxChunks) {
      this.stats.splitsBlockedByBudget++;
      return false;
    }
    if (!this.visible(n)) return false;
    return this.projectedError(n) > this.splitPx;
  }

  private wantsMerge(n: TNode): boolean {
    if (this.inContact(n)) return false;
    // A node split to satisfy 2:1 balance holds for a while so it can't
    // oscillate while the neighbor that needed it is still generating.
    if (n.forceSplitAt >= 0 && this.frame - n.forceSplitAt < 32) return false;
    for (const c of n.children!) if (c.forceSplitAt >= this.frame - 1) return false;
    if (this.holdCoarse) return true;
    const e = this.projectedError(n);
    if (!this.visible(n)) return e < this.splitPx * 2;
    return e < this.splitPx * 0.5 || this.renderedLeaves > this.maxChunks + 12;
  }

  private split(n: TNode): void {
    const lvl = n.level + 1;
    const kids: TNode[] = [];
    for (let cy = 0; cy < 2; cy++) {
      for (let cx = 0; cx < 2; cx++) {
        const c = new TNode(n.face, lvl, n.x * 2 + cx, n.y * 2 + cy, n);
        c.data = this.store.get(c.key) ?? null;
        // Start on the parent's surface and morph to the final shape.
        const contact = this.contactKeys.has(c.key);
        c.morph = contact ? 0 : 1;
        c.morphVel = contact ? 0 : -1;
        kids.push(c);
      }
    }
    n.children = kids;
    for (const c of kids) {
      this.ensureMesh(c);
      if (c.morphVel !== 0) this.morphing.add(c);
    }
    this.disposeMesh(n);
    this.renderedLeaves += 3;
  }

  private finishMerge(n: TNode): void {
    // A neighbor may have refined during the morph: re-validate 2:1 balance.
    if (!this.balanceAllowsMerge(n)) {
      n.merging = false;
      for (const c of n.children!) {
        c.morphVel = -1;
        this.morphing.add(c);
      }
      return;
    }
    n.data = n.data ?? this.store.get(n.key) ?? null;
    if (!n.data) return; // wait for data
    this.meshBudgetLeft = Math.max(this.meshBudgetLeft, 1);
    n.morph = 0;
    if (!this.ensureMesh(n)) return;
    for (const c of n.children!) this.disposeMesh(c);
    n.children = null;
    n.merging = false;
  }

  /** Advance geomorphs (call every frame). */
  updateMorphs(dt: number): void {
    const step = dt / MORPH_TIME;
    const doneParents = new Set<TNode>();
    for (const n of this.morphing) {
      if (this.contactKeys.has(n.key) && n.morphVel <= 0) {
        n.morph = 0;
        n.morphVel = 0;
      } else {
        n.morph = Math.max(0, Math.min(1, n.morph + n.morphVel * step));
      }
      if (n.mesh) n.mesh.material = this.materials[this.morphIndex(n.morph)];
      if ((n.morphVel < 0 && n.morph <= 0) || (n.morphVel > 0 && n.morph >= 1) || n.morphVel === 0) {
        if (n.morphVel > 0 && n.parent?.merging) doneParents.add(n.parent);
        n.morphVel = 0;
        this.morphing.delete(n);
      }
    }
    for (const p of doneParents) {
      if (p.children && p.children.every((c) => c.morph >= 1 && c.morphVel === 0)) this.finishMerge(p);
    }
    // Merges that completed their morph earlier but waited for data/budget.
    for (const n of this.meshNodes) {
      const p = n.parent;
      if (p && p.merging && p.children && p.children.every((c) => c.morph >= 1 && c.morphVel === 0)) this.finishMerge(p);
    }
  }

  /** Mark tiles as contact (collision) tiles; they snap to unmorphed geometry. */
  setContactKeys(keys: Set<string>): void {
    this.contactKeys = keys;
  }

  private updatePinned(): void {
    const pinned = new Set<string>();
    for (const n of this.meshNodes) pinned.add(n.key);
    for (const k of this.contactKeys) pinned.add(k);
    // Keep parents of rendered nodes to allow quick merges.
    for (const n of this.meshNodes) if (n.parent) pinned.add(n.parent.key);
    this.store.pinned = pinned;
  }

  private updateStats(): void {
    let leaves = 0;
    let maxL = 0;
    const walk = (n: TNode) => {
      if (n.isLeaf) {
        leaves++;
        if (n.level > maxL) maxL = n.level;
      } else for (const c of n.children!) walk(c);
    };
    for (const r of this.roots) walk(r);
    this.stats.leaves = leaves;
    this.stats.rendered = this.meshNodes.size;
    this.stats.morphing = this.morphing.size;
    this.stats.triangles = this.meshNodes.size * (6912 / 3);
    this.stats.maxLevel = maxL;
  }

  /** Apply horizon culling to meshes (frustum culling is done by Three). */
  cullMeshes(view: TerrainView): void {
    let culled = 0;
    for (const n of this.meshNodes) {
      const d = n.data!;
      _c.set(d.center[0] + d.bounds[0], d.center[1] + d.bounds[1], d.center[2] + d.bounds[2]);
      const hidden = this.horizonCulling && horizonCulled(_c.x, _c.y, _c.z, d.bounds[3], view.camPlanet, this.def.radius * 0.999);
      n.mesh!.visible = !hidden;
      if (hidden) culled++;
    }
    this.stats.horizonCulled = culled;
  }

  /** Leaf node data covering a planet-relative direction (for queries/tests). */
  leafForDir(x: number, y: number, z: number): TNode {
    const f = dirToFace(x, y, z);
    return this.leafAt(f.face, f.u, f.v);
  }

  /** Iterate rendered leaves (tests/diagnostics). */
  forEachMeshNode(fn: (n: TNode) => void): void {
    for (const n of this.meshNodes) fn(n);
  }

  dispose(): void {
    for (const n of [...this.meshNodes]) this.disposeMesh(n);
    this.morphing.clear();
    for (const r of this.roots) r.children = null;
  }
}

