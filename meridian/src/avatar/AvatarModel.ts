import {
  Bone,
  BoxGeometry,
  BufferGeometry,
  Color,
  CylinderGeometry,
  Float32BufferAttribute,
  Group,
  LatheGeometry,
  Matrix4,
  MeshStandardMaterial,
  Skeleton,
  SkinnedMesh,
  SphereGeometry,
  TorusGeometry,
  Uint16BufferAttribute,
  Vector2,
  Vector3,
} from 'three';
import { mergeGeometries } from 'three/addons/utils/BufferGeometryUtils.js';

// Explorer character built in code: one Skeleton shared by a few SkinnedMeshes
// (one per material). Model frame: feet on y = 0, up = +Y, forward = -Z,
// right = +X (the ship's convention). Rest pose: standing, arms down.

/** Bone indices (the order of AvatarRig.bones). */
export const B = {
  root: 0,
  hips: 1,
  spine: 2,
  chest: 3,
  head: 4,
  upperArmL: 5,
  lowerArmL: 6,
  handL: 7,
  upperArmR: 8,
  lowerArmR: 9,
  handR: 10,
  upperLegL: 11,
  lowerLegL: 12,
  footL: 13,
  upperLegR: 14,
  lowerLegR: 15,
  footR: 16,
} as const;
export type BoneName = keyof typeof B;

/** Body dimensions (m). Total height 1.8 m to match the walking capsule. */
export const DIM = {
  height: 1.8,
  hipY: 0.94,
  hipX: 0.1,
  thigh: 0.43,
  shin: 0.42,
  ankleY: 0.09,
  shoulderX: 0.215,
  shoulderY: 1.45,
  upperArm: 0.29,
  forearm: 0.26,
  /** Head pivot (base of the neck). */
  neckY: 1.53,
  /** Eye height in the rest pose (matches WALK.eye). */
  eyeY: 1.62,
} as const;

// Parent and rest offset (from the parent's origin) of every bone.
const REST: Record<BoneName, [BoneName | null, number, number, number]> = {
  root: [null, 0, 0, 0],
  hips: ['root', 0, DIM.hipY, 0],
  spine: ['hips', 0, 0.13, 0],
  chest: ['spine', 0, 0.2, 0],
  head: ['chest', 0, DIM.neckY - DIM.hipY - 0.33, 0],
  upperArmL: ['chest', -DIM.shoulderX, DIM.shoulderY - DIM.hipY - 0.33, 0],
  lowerArmL: ['upperArmL', 0, -DIM.upperArm, 0],
  handL: ['lowerArmL', 0, -DIM.forearm, 0],
  upperArmR: ['chest', DIM.shoulderX, DIM.shoulderY - DIM.hipY - 0.33, 0],
  lowerArmR: ['upperArmR', 0, -DIM.upperArm, 0],
  handR: ['lowerArmR', 0, -DIM.forearm, 0],
  upperLegL: ['hips', -DIM.hipX, -0.02, 0],
  lowerLegL: ['upperLegL', 0, -DIM.thigh, 0],
  footL: ['lowerLegL', 0, -DIM.shin, 0],
  upperLegR: ['hips', DIM.hipX, -0.02, 0],
  lowerLegR: ['upperLegR', 0, -DIM.thigh, 0],
  footR: ['lowerLegR', 0, -DIM.shin, 0],
};

export const BONE_NAMES = Object.keys(B) as BoneName[];

/** Rest world (model-space) position of a bone. */
export function restPosition(name: BoneName, out = new Vector3()): Vector3 {
  out.set(0, 0, 0);
  let n: BoneName | null = name;
  while (n) {
    const r: [BoneName | null, number, number, number] = REST[n];
    out.x += r[1];
    out.y += r[2];
    out.z += r[3];
    n = r[0];
  }
  return out;
}

/** Suit palette: slate fabric, off-white plates, amber accents, graphite seals, gold visor, teal status lights. */
export type SuitPart = 'fabric' | 'plate' | 'accent' | 'seal' | 'visor' | 'light';

export interface AvatarRig {
  /** Model root (feet at its origin). */
  readonly root: Group;
  readonly bones: Bone[];
  readonly skeleton: Skeleton;
  readonly meshes: SkinnedMesh[];
  readonly materials: Record<SuitPart, MeshStandardMaterial>;
  dispose(): void;
}

// ---------------------------------------------------------------- geometry helpers

/** Smooth step weight. */
function sstep(a: number, b: number, x: number): number {
  const t = Math.min(1, Math.max(0, (x - a) / (b - a)));
  return t * t * (3 - 2 * t);
}

/**
 * Tapered capsule along -Y from y = 0 (radius r0) to y = -len (radius r1),
 * with rounded ends. Built as a lathe so normals are smooth.
 */
function taper(r0: number, r1: number, len: number, radial = 12, sz = 1): BufferGeometry {
  const pts: Vector2[] = [];
  const cap = 4;
  for (let i = 0; i <= cap; i++) {
    const a = -Math.PI / 2 + (i / cap) * (Math.PI / 2);
    pts.push(new Vector2(Math.max(1e-3, Math.cos(a) * r1), -len + Math.sin(a) * r1 * 0.8));
  }
  for (let i = 1; i <= cap; i++) {
    const a = (i / cap) * (Math.PI / 2);
    pts.push(new Vector2(Math.max(1e-3, Math.cos(a) * r0), Math.sin(a) * r0 * 0.8));
  }
  const g = new LatheGeometry(pts, radial);
  if (sz !== 1) g.scale(1, 1, sz);
  return g;
}

/** Lathe from a (radius, y) profile listed bottom to top; optional depth scale. */
function lathe(profile: [number, number][], radial = 16, sz = 1): BufferGeometry {
  const g = new LatheGeometry(profile.map(([r, y]) => new Vector2(Math.max(1e-3, r), y)), radial);
  if (sz !== 1) g.scale(1, 1, sz);
  return g;
}

/**
 * Write skin attributes. Each vertex is bound to `bone`, blended toward
 * `parent` with weight 1 at y = y1 falling to 0 at y = y0 (model space), so
 * joints bend smoothly. Without a parent the part is rigid.
 */
function skin(g: BufferGeometry, bone: number, parent?: number, y0 = 0, y1 = 0): BufferGeometry {
  const geo = g.index ? g.toNonIndexed() : g;
  if (geo !== g) g.dispose();
  const pos = geo.getAttribute('position');
  const n = pos.count;
  const idx = new Uint16Array(n * 4);
  const w = new Float32Array(n * 4);
  for (let i = 0; i < n; i++) {
    idx[i * 4] = bone;
    if (parent === undefined) {
      w[i * 4] = 1;
      continue;
    }
    const y = pos.getY(i);
    // Weight toward the parent: 1 at y1 (joint side), 0 at y0.
    const tp = y1 > y0 ? sstep(y0, y1, y) : 1 - sstep(y1, y0, y);
    const wp = 0.5 * tp;
    idx[i * 4 + 1] = parent;
    w[i * 4] = 1 - wp;
    w[i * 4 + 1] = wp;
  }
  geo.setAttribute('skinIndex', new Uint16BufferAttribute(idx, 4));
  geo.setAttribute('skinWeight', new Float32BufferAttribute(w, 4));
  if (!geo.getAttribute('uv')) geo.setAttribute('uv', new Float32BufferAttribute(new Float32Array(n * 2), 2));
  return geo;
}

/** Translate a geometry into model space. */
function place(g: BufferGeometry, x: number, y: number, z: number): BufferGeometry {
  g.translate(x, y, z);
  return g;
}

function rot(g: BufferGeometry, rx: number, ry: number, rz: number): BufferGeometry {
  if (rx) g.rotateX(rx);
  if (ry) g.rotateY(ry);
  if (rz) g.rotateZ(rz);
  return g;
}

// ---------------------------------------------------------------- the explorer

/**
 * Build the explorer: an original survey suit with a slate fabric under-layer,
 * off-white hard plates (chest, shoulders, shins, backpack, helmet), amber
 * edge accents, graphite seals and boots, a gold visor and teal status lights.
 */
export function buildAvatar(): AvatarRig {
  const parts: Record<SuitPart, BufferGeometry[]> = { fabric: [], plate: [], accent: [], seal: [], visor: [], light: [] };
  const add = (p: SuitPart, g: BufferGeometry) => parts[p].push(g);
  const P = (n: BoneName) => restPosition(n);

  // --- Pelvis and torso (fabric), belt (seal).
  const hipY = DIM.hipY;
  add('fabric', skin(lathe([[0.02, hipY - 0.12], [0.13, hipY - 0.1], [0.165, hipY - 0.03], [0.165, hipY + 0.06], [0.15, hipY + 0.13]], 18, 0.72), B.hips));
  add('fabric', skin(lathe([[0.15, hipY + 0.1], [0.145, hipY + 0.2], [0.16, hipY + 0.3]], 18, 0.7), B.spine, B.hips, hipY + 0.2, hipY + 0.08));
  add('seal', skin(place(new TorusGeometry(0.155, 0.022, 6, 22).rotateX(Math.PI / 2).scale(1, 1, 0.74), 0, hipY + 0.07, 0), B.hips));
  // Chest: wide, slightly deeper at the front.
  add('fabric', skin(lathe([[0.16, hipY + 0.29], [0.19, hipY + 0.38], [0.205, hipY + 0.47], [0.19, hipY + 0.54], [0.12, hipY + 0.58], [0.06, hipY + 0.6]], 18, 0.66), B.chest, B.spine, hipY + 0.3, hipY + 0.36));
  // Chest plate (front) with an amber edge strip and a teal status light.
  add('plate', skin(place(rot(lathe([[0.04, -0.13], [0.16, -0.1], [0.18, 0.0], [0.15, 0.09], [0.04, 0.11]], 16, 0.35), 0, 0, 0), 0, hipY + 0.45, -0.06), B.chest));
  add('accent', skin(place(new BoxGeometry(0.2, 0.022, 0.03), 0, hipY + 0.345, -0.118), B.chest));
  add('light', skin(place(new BoxGeometry(0.05, 0.018, 0.012), 0.07, hipY + 0.48, -0.127), B.chest));
  add('light', skin(place(new BoxGeometry(0.05, 0.018, 0.012), 0.07, hipY + 0.455, -0.126), B.chest));
  // Collar ring (seal) where the helmet meets the suit.
  add('seal', skin(place(new TorusGeometry(0.105, 0.03, 8, 22).rotateX(Math.PI / 2), 0, DIM.neckY + 0.02, 0.0), B.chest));

  // --- Backpack (life support): plate shell, seal frame, amber stripes, teal lights.
  add('plate', skin(place(new BoxGeometry(0.34, 0.42, 0.16, 2, 2, 1), 0, hipY + 0.39, 0.205), B.chest));
  add('seal', skin(place(new BoxGeometry(0.36, 0.06, 0.18), 0, hipY + 0.17, 0.2), B.chest));
  add('seal', skin(place(new CylinderGeometry(0.045, 0.045, 0.38, 10).rotateZ(Math.PI / 2), 0, hipY + 0.62, 0.2), B.chest));
  add('accent', skin(place(new BoxGeometry(0.03, 0.36, 0.012), -0.12, hipY + 0.39, 0.29), B.chest));
  add('accent', skin(place(new BoxGeometry(0.03, 0.36, 0.012), 0.12, hipY + 0.39, 0.29), B.chest));
  for (let i = 0; i < 3; i++) add('light', skin(place(new BoxGeometry(0.035, 0.035, 0.01), -0.04 + i * 0.04, hipY + 0.52, 0.289), B.chest));

  // --- Helmet: plate shell, gold visor, seal rim, amber crest.
  const headC = new Vector3(0, DIM.eyeY + 0.02, 0);
  add('plate', skin(place(new SphereGeometry(0.155, 22, 16).scale(0.96, 1.05, 1.02), headC.x, headC.y, headC.z), B.head));
  // Visor: front cap of a slightly larger sphere.
  add('visor', skin(place(new SphereGeometry(0.162, 22, 12, Math.PI * 0.62, Math.PI * 0.76, Math.PI * 0.26, Math.PI * 0.4).scale(0.96, 1.0, 1.04), headC.x, headC.y - 0.005, headC.z), B.head));
  add('seal', skin(place(new TorusGeometry(0.152, 0.012, 6, 28, Math.PI * 0.9).rotateY(Math.PI * 0.55).rotateZ(0), headC.x, headC.y - 0.06, headC.z), B.head));
  add('accent', skin(place(new BoxGeometry(0.03, 0.025, 0.24), 0, headC.y + 0.155, 0.02), B.head));
  add('light', skin(place(new BoxGeometry(0.02, 0.02, 0.03), -0.14, headC.y + 0.02, -0.04), B.head));

  // --- Arms.
  for (const side of [-1, 1] as const) {
    const ua = side < 0 ? B.upperArmL : B.upperArmR;
    const la = side < 0 ? B.lowerArmL : B.lowerArmR;
    const hd = side < 0 ? B.handL : B.handR;
    const s = P(side < 0 ? 'upperArmL' : 'upperArmR');
    const e = P(side < 0 ? 'lowerArmL' : 'lowerArmR');
    const w = P(side < 0 ? 'handL' : 'handR');
    add('fabric', skin(place(taper(0.064, 0.052, DIM.upperArm, 12), s.x, s.y, s.z), ua, B.chest, s.y - 0.06, s.y + 0.04));
    // Shoulder pad (plate) + amber trim.
    add('plate', skin(place(new SphereGeometry(0.088, 14, 10, 0, Math.PI * 2, 0, Math.PI * 0.55).scale(1.05, 0.9, 1.1), s.x + side * 0.012, s.y + 0.01, s.z), ua));
    add('accent', skin(place(new TorusGeometry(0.08, 0.009, 5, 18).rotateX(Math.PI / 2), s.x + side * 0.012, s.y - 0.02, s.z), ua));
    // Elbow seal, forearm, forearm plate.
    add('seal', skin(place(new SphereGeometry(0.052, 10, 8), e.x, e.y, e.z), la, ua, e.y - 0.02, e.y + 0.03));
    add('fabric', skin(place(taper(0.05, 0.04, DIM.forearm - 0.04, 12), e.x, e.y - 0.01, e.z), la, ua, e.y - 0.05, e.y + 0.01));
    add('plate', skin(place(taper(0.054, 0.046, 0.11, 12), e.x, e.y - 0.1, e.z), la));
    add('light', skin(place(new BoxGeometry(0.012, 0.03, 0.03), e.x - side * 0.05, e.y - 0.15, e.z - 0.01), la));
    // Glove (seal): palm block with a thumb.
    add('seal', skin(place(taper(0.045, 0.035, 0.06, 10), w.x, w.y + 0.005, w.z), hd, la, w.y - 0.01, w.y + 0.02));
    add('seal', skin(place(new BoxGeometry(0.035, 0.09, 0.075), w.x, w.y - 0.075, w.z), hd));
    add('seal', skin(place(new BoxGeometry(0.02, 0.05, 0.022).rotateZ(side * 0.3), w.x - side * 0.022, w.y - 0.05, w.z - 0.04), hd));
  }

  // --- Legs.
  for (const side of [-1, 1] as const) {
    const ul = side < 0 ? B.upperLegL : B.upperLegR;
    const ll = side < 0 ? B.lowerLegL : B.lowerLegR;
    const ft = side < 0 ? B.footL : B.footR;
    const h = P(side < 0 ? 'upperLegL' : 'upperLegR');
    const k = P(side < 0 ? 'lowerLegL' : 'lowerLegR');
    const a = P(side < 0 ? 'footL' : 'footR');
    add('fabric', skin(place(taper(0.092, 0.066, DIM.thigh, 14), h.x, h.y, h.z), ul, B.hips, h.y - 0.09, h.y + 0.03));
    // Thigh pocket (accent).
    add('accent', skin(place(new BoxGeometry(0.02, 0.1, 0.08), h.x + side * 0.09, h.y - 0.2, h.z), ul));
    // Knee guard (plate) and knee seal.
    add('seal', skin(place(new SphereGeometry(0.066, 12, 8), k.x, k.y, k.z), ll, ul, k.y - 0.03, k.y + 0.04));
    add('plate', skin(place(new SphereGeometry(0.062, 12, 8, Math.PI * 0.55, Math.PI * 0.9).scale(1, 1.25, 1), k.x, k.y + 0.005, k.z - 0.012), ll));
    // Shin and its plate.
    add('fabric', skin(place(taper(0.06, 0.05, DIM.shin - 0.05, 14), k.x, k.y - 0.02, k.z), ll, ul, k.y - 0.06, k.y + 0.02));
    add('plate', skin(place(rot(taper(0.066, 0.058, 0.2, 14, 0.85), 0, 0, 0), k.x, k.y - 0.12, k.z - 0.004), ll));
    add('accent', skin(place(new BoxGeometry(0.03, 0.12, 0.012), k.x, k.y - 0.2, k.z - 0.067), ll));
    // Boot (seal): cuff, foot block with toe cap, sole.
    add('seal', skin(place(taper(0.064, 0.06, 0.07, 12), a.x, a.y + 0.06, a.z), ft, ll, a.y + 0.02, a.y + 0.07));
    add('seal', skin(place(new BoxGeometry(0.11, 0.075, 0.24), a.x, 0.045, a.z - 0.045), ft));
    add('plate', skin(place(new BoxGeometry(0.105, 0.04, 0.07), a.x, 0.065, a.z - 0.135), ft));
    add('accent', skin(place(new BoxGeometry(0.116, 0.014, 0.25), a.x, 0.007, a.z - 0.045), ft));
  }

  // --- Materials (MeshStandardMaterial: the same PBR path as the ship).
  const materials: Record<SuitPart, MeshStandardMaterial> = {
    fabric: new MeshStandardMaterial({ color: 0x4b5566, roughness: 0.86, metalness: 0.0, envMapIntensity: 0.6 }),
    plate: new MeshStandardMaterial({ color: 0xe8e3d8, roughness: 0.38, metalness: 0.05, envMapIntensity: 0.9 }),
    accent: new MeshStandardMaterial({ color: 0xe07a24, roughness: 0.5, metalness: 0.1, envMapIntensity: 0.7 }),
    seal: new MeshStandardMaterial({ color: 0x23262c, roughness: 0.62, metalness: 0.25, envMapIntensity: 0.7 }),
    visor: new MeshStandardMaterial({ color: 0xc69a45, roughness: 0.1, metalness: 0.95, envMapIntensity: 1.4, emissive: new Color(0x1a1206), emissiveIntensity: 1 }),
    light: new MeshStandardMaterial({ color: 0x0b2a2a, emissive: new Color(0x3fe6d2), emissiveIntensity: 2.4, roughness: 0.4 }),
  };

  // --- Bones in the rest pose.
  const bones: Bone[] = [];
  for (const name of BONE_NAMES) {
    const b = new Bone();
    b.name = name;
    const r = REST[name];
    b.position.set(r[1], r[2], r[3]);
    bones.push(b);
  }
  for (const name of BONE_NAMES) {
    const parent = REST[name][0];
    if (parent) bones[B[parent]].add(bones[B[name]]);
  }
  const root = new Group();
  root.name = 'explorer';
  root.add(bones[B.root]);
  root.updateMatrixWorld(true);
  const skeleton = new Skeleton(bones);
  const meshes: SkinnedMesh[] = [];
  for (const key of Object.keys(parts) as SuitPart[]) {
    const merged = mergeGeometries(parts[key], false);
    for (const g of parts[key]) g.dispose();
    if (!merged) continue;
    merged.computeBoundingSphere();
    const m = new SkinnedMesh(merged, materials[key]);
    m.name = `explorer-${key}`;
    m.castShadow = key !== 'light' && key !== 'visor';
    m.receiveShadow = true;
    // Limbs swing outside the bind-pose bounds; the character is small and always near the camera.
    m.frustumCulled = false;
    root.add(m);
    m.bind(skeleton, new Matrix4());
    meshes.push(m);
  }
  return {
    root,
    bones,
    skeleton,
    meshes,
    materials,
    dispose() {
      for (const m of meshes) m.geometry.dispose();
      for (const k of Object.keys(materials) as SuitPart[]) materials[k].dispose();
      skeleton.dispose();
      root.removeFromParent();
    },
  };
}
