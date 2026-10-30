import {
  BufferGeometry,
  Color,
  ConeGeometry,
  CylinderGeometry,
  Float32BufferAttribute,
  IcosahedronGeometry,
  Matrix4,
  Quaternion,
  SphereGeometry,
  Vector3,
} from 'three';
import { mergeGeometries } from 'three/addons/utils/BufferGeometryUtils.js';
import { mulberry32 } from '../core/rng';

// Procedural species meshes. All are modeled in a unit frame (base at the
// origin, +Y up, height ~1) and scaled per instance. Vertex colors carry the
// species palette; instance colors add per-instance tint variation.

function colorize(g: BufferGeometry, fn: (p: Vector3, n: Vector3, c: Color) => void): BufferGeometry {
  const pos = g.attributes.position;
  const nor = g.attributes.normal;
  const cols = new Float32Array(pos.count * 3);
  const p = new Vector3();
  const n = new Vector3();
  const c = new Color();
  for (let i = 0; i < pos.count; i++) {
    p.fromBufferAttribute(pos, i);
    n.fromBufferAttribute(nor, i);
    fn(p, n, c);
    cols[i * 3] = c.r;
    cols[i * 3 + 1] = c.g;
    cols[i * 3 + 2] = c.b;
  }
  g.setAttribute('color', new Float32BufferAttribute(cols, 3));
  return g;
}

function prep(g: BufferGeometry): BufferGeometry {
  const ng = g.index ? g.toNonIndexed() : g;
  for (const k of Object.keys(ng.attributes)) if (k !== 'position' && k !== 'normal' && k !== 'color') ng.deleteAttribute(k);
  ng.computeVertexNormals();
  return ng;
}

function merge(parts: BufferGeometry[]): BufferGeometry {
  const g = mergeGeometries(parts.map(prep), false);
  if (!g) throw new Error('prop merge failed');
  g.computeBoundingSphere();
  return g;
}

const lin = (hex: number) => new Color(hex).convertSRGBToLinear();

/** Displace an icosphere into an irregular rock (deterministic). */
function rockGeo(detail: number, seed: number, squash: number): BufferGeometry {
  const g = new IcosahedronGeometry(1, detail);
  const rnd = mulberry32(seed);
  const bumps: [Vector3, number][] = [];
  for (let i = 0; i < 7; i++) bumps.push([new Vector3(rnd() - 0.5, rnd() - 0.5, rnd() - 0.5).normalize(), 0.12 + rnd() * 0.22]);
  const p = g.attributes.position;
  const v = new Vector3();
  for (let i = 0; i < p.count; i++) {
    v.fromBufferAttribute(p, i);
    const d = v.clone().normalize();
    let r = 1;
    for (const [b, a] of bumps) r += a * Math.max(0, d.dot(b)) ** 3 - a * 0.35 * Math.max(0, -d.dot(b)) ** 4;
    // Flatten facets slightly for a fractured look.
    r = Math.round(r * 6) / 6 * 0.4 + r * 0.6;
    v.copy(d).multiplyScalar(r);
    v.y = v.y * squash;
    p.setXYZ(i, v.x, v.y + squash * 0.55, v.z);
  }
  g.computeVertexNormals();
  return g;
}

function crystal(radius: number, length: number, tilt: Vector3, offset: Vector3, sides = 6): BufferGeometry {
  const g = new CylinderGeometry(radius * 0.75, radius, length, sides, 1);
  const tip = new ConeGeometry(radius * 0.75, length * 0.28, sides, 1);
  tip.translate(0, length * 0.64, 0);
  const m = merge([g, tip]);
  m.translate(0, length / 2, 0);
  const q = new Quaternion().setFromUnitVectors(new Vector3(0, 1, 0), tilt.clone().normalize());
  m.applyMatrix4(new Matrix4().makeRotationFromQuaternion(q));
  m.translate(offset.x, offset.y, offset.z);
  return m;
}

export interface SpeciesGeometry {
  lod0: BufferGeometry;
  lod1: BufferGeometry | null;
}

// ------------------------------------------------------------------ Ilex

/** Lantern-tree: a flared, curving trunk under an irregular cluster of teal canopy lobes. Height 1. */
export function lanternTree(): SpeciesGeometry {
  const trunkC = lin(0x6a5444);
  const topC = lin(0x2c6a60);
  const midC = lin(0x3f8676);
  const underC = lin(0x9fd8c4);
  // Both LODs share one lobe layout so the switch does not change the silhouette.
  const make = (radial: number, lobeCount: number, detail: boolean) => {
    const trunk = new CylinderGeometry(0.016, 0.036, 0.8, radial, detail ? 4 : 1, !detail);
    trunk.translate(0, 0.4, 0);
    const tp = trunk.attributes.position;
    for (let i = 0; i < tp.count; i++) {
      const y = tp.getY(i);
      const t = y / 0.8;
      // Flared base and a gentle S-curve.
      const flare = 1 + 0.9 * Math.max(0, 0.12 - t) / 0.12;
      tp.setX(i, tp.getX(i) * flare + 0.07 * t * t - 0.02 * Math.sin(t * 3));
      tp.setZ(i, tp.getZ(i) * flare);
    }
    colorize(trunk, (_p, _n, c) => c.copy(trunkC));
    const parts: BufferGeometry[] = [trunk];
    const rnd = mulberry32(3);
    // Irregular umbrella: one crown lobe plus satellites at different heights.
    for (let k = 0; k < lobeCount; k++) {
      const a = (k / lobeCount) * Math.PI * 2 + rnd() * 0.6;
      const ring = k === 0 ? 0 : 0.11 + rnd() * 0.08;
      const r = k === 0 ? 0.2 : 0.11 + rnd() * 0.07;
      const y = k === 0 ? 0.86 : 0.72 + rnd() * 0.14;
      const cap = new SphereGeometry(1, detail ? 9 : 6, detail ? 5 : 2);
      cap.scale(r, r * (0.34 + rnd() * 0.1), r);
      cap.translate(0.07 + Math.cos(a) * ring, y, Math.sin(a) * ring);
      colorize(cap, (p, n, c) => {
        const t = n.y * 0.5 + 0.5;
        // Pale luminous undersides, darker crowns, lighter rims.
        c.copy(underC).lerp(midC, Math.min(1, t * 1.6)).lerp(topC, Math.max(0, t - 0.6) * 2.2);
        void p;
      });
      parts.push(cap);
    }
    return merge(parts);
  };
  return { lod0: make(8, 6, true), lod1: make(4, 6, false) };
}

/** Chalk spire / boulder: pale fractured rock, elongated vertically. Height ~1. */
export function chalkSpire(): SpeciesGeometry {
  const a = lin(0xefe9dc);
  const b = lin(0xb8b0a0);
  const tint = (g: BufferGeometry) =>
    colorize(g, (p, n, c) => {
      const band = 0.5 + 0.5 * Math.sin(p.y * 9.0 + p.x * 2.0);
      c.copy(b).lerp(a, 0.55 + 0.45 * band * Math.max(0.2, n.y * 0.5 + 0.5));
    });
  const l0 = tint(rockGeo(2, 11, 1.6));
  const l1 = tint(rockGeo(0, 11, 1.6));
  l0.scale(0.42, 0.62, 0.42);
  l1.scale(0.42, 0.62, 0.42);
  return { lod0: merge([l0]), lod1: merge([l1]) };
}

/** Ochre fan-shrub: radiating flat blades. Height ~1. */
export function fanShrub(): SpeciesGeometry {
  const base = lin(0x8d7638);
  const tip = lin(0xe6bd62);
  const blades: BufferGeometry[] = [];
  const rnd = mulberry32(5);
  for (let i = 0; i < 7; i++) {
    const a = (i / 7) * Math.PI * 2 + rnd() * 0.4;
    const lean = 0.35 + rnd() * 0.35;
    const g = new BufferGeometry();
    const w = 0.09 + rnd() * 0.05;
    const h = 0.75 + rnd() * 0.3;
    // A thin blade: two triangles, double-sided by duplication.
    const v = [-w, 0, 0, w, 0, 0, 0, h, lean * h * 0.5, -w * 0.4, h * 0.65, lean * h * 0.3, w * 0.4, h * 0.65, lean * h * 0.3];
    const idx = [0, 1, 4, 0, 4, 3, 3, 4, 2, 1, 0, 3, 1, 3, 4, 4, 3, 2];
    const pos: number[] = [];
    for (const k of idx) pos.push(v[k * 3], v[k * 3 + 1], v[k * 3 + 2]);
    g.setAttribute('position', new Float32BufferAttribute(pos, 3));
    g.computeVertexNormals();
    g.rotateY(a);
    colorize(g, (p, _n, c) => c.copy(base).lerp(tip, Math.min(1, p.y / 0.9)));
    blades.push(g);
  }
  return { lod0: merge(blades), lod1: null };
}

// ---------------------------------------------------------------- Vesper

/** Black glass outcrop: a cluster of glossy dark crystals. Height ~1. */
export function blackGlass(): SpeciesGeometry {
  const dark = lin(0x0f0f12);
  const sheen = lin(0x3a2f45);
  const make = (count: number, sides: number) => {
    const rnd = mulberry32(21);
    const parts: BufferGeometry[] = [];
    for (let i = 0; i < count; i++) {
      const tilt = new Vector3((rnd() - 0.5) * 0.9, 1, (rnd() - 0.5) * 0.9);
      const off = new Vector3((rnd() - 0.5) * 0.5, 0, (rnd() - 0.5) * 0.5);
      parts.push(crystal(0.08 + rnd() * 0.08, 0.45 + rnd() * 0.55, tilt, off, sides));
    }
    const g = merge(parts);
    return colorize(g, (p, _n, c) => c.copy(dark).lerp(sheen, Math.min(1, p.y * 0.8)));
  };
  return { lod0: make(7, 6), lod1: make(3, 4) };
}

/** Rust hoodoo pillar: stacked drums under a darker cap rock. Height 1. */
export function rustPillar(): SpeciesGeometry {
  const c1 = lin(0x8e4126);
  const c2 = lin(0xb46a40);
  const cap = lin(0x4a2418);
  const make = (radial: number) => {
    const drums: BufferGeometry[] = [];
    const spec: [number, number, number, number][] = [[0, 0.3, 0.2, 0.17], [0.3, 0.3, 0.17, 0.13], [0.6, 0.27, 0.13, 0.1]];
    for (const [y, h, r0, r1] of spec) {
      const d = new CylinderGeometry(r1, r0, h, radial, 2);
      d.translate(0, y + h / 2, 0);
      drums.push(d);
    }
    const top = new CylinderGeometry(0.2, 0.16, 0.1, radial, 1);
    top.translate(0.02, 0.92, 0);
    const g = merge([...drums, top]);
    return colorize(g, (p, _n, c) => {
      if (p.y > 0.86) c.copy(cap);
      else c.copy(c1).lerp(c2, 0.5 + 0.5 * Math.sin(p.y * 38));
    });
  };
  return { lod0: make(10), lod1: make(5) };
}

/** Pale dune bristle tuft. Height ~1. */
export function duneBristle(): SpeciesGeometry {
  const base = lin(0x8a7a5a);
  const tip = lin(0xe8dcc0);
  const rnd = mulberry32(31);
  const parts: BufferGeometry[] = [];
  for (let i = 0; i < 9; i++) {
    const c = new ConeGeometry(0.025, 0.8 + rnd() * 0.3, 3, 1);
    c.translate(0, 0.45, 0);
    c.rotateZ((rnd() - 0.5) * 0.9);
    c.rotateX((rnd() - 0.5) * 0.9);
    c.translate((rnd() - 0.5) * 0.15, 0, (rnd() - 0.5) * 0.15);
    parts.push(c);
  }
  const g = merge(parts);
  colorize(g, (p, _n, col) => col.copy(base).lerp(tip, Math.min(1, p.y)));
  return { lod0: g, lod1: null };
}

// ----------------------------------------------------------------- Cairn

/** Rime shard cluster: pale blue ice crystals. Height ~1. */
export function rimeShard(): SpeciesGeometry {
  const deep = lin(0x6f9ccc);
  const pale = lin(0xe6f2ff);
  const make = (count: number, sides: number) => {
    const rnd = mulberry32(41);
    const parts: BufferGeometry[] = [];
    for (let i = 0; i < count; i++) {
      const tilt = new Vector3((rnd() - 0.5) * 1.1, 1, (rnd() - 0.5) * 1.1);
      const off = new Vector3((rnd() - 0.5) * 0.6, 0, (rnd() - 0.5) * 0.6);
      parts.push(crystal(0.07 + rnd() * 0.09, 0.4 + rnd() * 0.6, tilt, off, sides));
    }
    const g = merge(parts);
    return colorize(g, (p, n, c) => c.copy(deep).lerp(pale, Math.min(1, 0.35 + p.y * 0.6 + Math.max(0, n.y) * 0.2)));
  };
  return { lod0: make(8, 5), lod1: make(3, 4) };
}

/** Silver breccia boulder. Height ~1. */
export function silverBoulder(): SpeciesGeometry {
  const a = lin(0x9a9da4);
  const b = lin(0x55585f);
  const tint = (g: BufferGeometry) =>
    colorize(g, (p, n, c) => c.copy(b).lerp(a, 0.4 + 0.4 * Math.max(0, n.y) + 0.2 * Math.sin(p.x * 12 + p.z * 7)));
  const l0 = tint(rockGeo(2, 51, 0.8));
  const l1 = tint(rockGeo(0, 51, 0.8));
  l0.scale(0.6, 0.62, 0.6);
  l1.scale(0.6, 0.62, 0.6);
  return { lod0: merge([l0]), lod1: merge([l1]) };
}

/** Small ejecta pebbles (near detail). */
export function pebbles(): SpeciesGeometry {
  const a = lin(0x8c8f95);
  const b = lin(0x4b4d52);
  const rnd = mulberry32(61);
  const parts: BufferGeometry[] = [];
  for (let i = 0; i < 5; i++) {
    const g = rockGeo(0, 70 + i, 0.6);
    const s = 0.12 + rnd() * 0.18;
    g.scale(s, s, s);
    g.translate((rnd() - 0.5) * 1.2, 0, (rnd() - 0.5) * 1.2);
    parts.push(g);
  }
  const g = merge(parts);
  colorize(g, (p, n, c) => c.copy(b).lerp(a, 0.4 + 0.5 * Math.max(0, n.y)));
  return { lod0: g, lod1: null };
}

// ------------------------------------------------------------------- Sol

/** Two-tone boulder (lighter where it faces up). Height ~1. */
function toneBoulder(light: number, dark: number, seed: number, squash: number): SpeciesGeometry {
  const a = lin(light);
  const b = lin(dark);
  const tint = (g: BufferGeometry) =>
    colorize(g, (p, n, c) => c.copy(b).lerp(a, 0.35 + 0.45 * Math.max(0, n.y) + 0.12 * Math.sin(p.x * 9 + p.z * 5)));
  const l0 = tint(rockGeo(2, seed, squash));
  const l1 = tint(rockGeo(0, seed, squash));
  l0.scale(0.6, 0.62, 0.6);
  l1.scale(0.6, 0.62, 0.6);
  return { lod0: merge([l0]), lod1: merge([l1]) };
}

/** Pebble cluster in two tones (near detail). */
function tonePebbles(light: number, dark: number, seed: number): SpeciesGeometry {
  const a = lin(light);
  const b = lin(dark);
  const rnd = mulberry32(seed);
  const parts: BufferGeometry[] = [];
  for (let i = 0; i < 6; i++) {
    const g = rockGeo(0, seed + 1 + i, 0.6);
    const s = 0.1 + rnd() * 0.2;
    g.scale(s, s, s);
    g.translate((rnd() - 0.5) * 1.3, 0, (rnd() - 0.5) * 1.3);
    parts.push(g);
  }
  const g = merge(parts);
  colorize(g, (_p, n, c) => c.copy(b).lerp(a, 0.4 + 0.5 * Math.max(0, n.y)));
  return { lod0: g, lod1: null };
}

/** Lunar boulder: grey ejecta block. */
export const lunarBoulder = (): SpeciesGeometry => toneBoulder(0x9d9b95, 0x5a5955, 83, 0.75);
/** Lunar regolith pebbles. */
export const lunarPebbles = (): SpeciesGeometry => tonePebbles(0x8f8d88, 0x4d4c49, 101);
/** Martian vesicular basalt: dark brown-grey under a film of dust. */
export const marsBasalt = (): SpeciesGeometry => toneBoulder(0x7a5d4a, 0x3a2c24, 91, 0.7);
/** Martian pebbles. */
export const marsPebbles = (): SpeciesGeometry => tonePebbles(0x8a6448, 0x3e2b20, 111);
/** Earth boulder (weathered grey rock). */
export const earthBoulder = (): SpeciesGeometry => toneBoulder(0x8e8b83, 0x54524c, 97, 0.8);

/** Needleleaf tree: a trunk under stacked cones. Height 1. */
export function conifer(): SpeciesGeometry {
  const bark = lin(0x5a4430);
  const dark = lin(0x2d5132);
  const light = lin(0x5c8f52);
  const make = (sides: number, tiers: number) => {
    const trunk = new CylinderGeometry(0.022, 0.035, 0.3, Math.max(3, sides - 2), 1);
    trunk.translate(0, 0.15, 0);
    const parts: BufferGeometry[] = [colorize(trunk, (_p, _n, c) => c.copy(bark))];
    for (let i = 0; i < tiers; i++) {
      const t = tiers > 1 ? i / (tiers - 1) : 0;
      const r = 0.22 * (1 - t * 0.5);
      const h = tiers > 1 ? 0.42 * (1 - t * 0.25) : 0.85;
      const cone = new ConeGeometry(r, h, sides, 1);
      cone.translate(0, 0.16 + t * 0.5 + h / 2, 0);
      parts.push(colorize(cone, (p, n, c) => c.copy(dark).lerp(light, Math.min(1, 0.25 + Math.max(0, n.y) * 0.5 + p.y * 0.2))));
    }
    return merge(parts);
  };
  return { lod0: make(7, 3), lod1: make(4, 1) };
}

/** Broadleaf tree: a trunk under a few rounded canopy lobes. Height 1. */
export function broadleaf(): SpeciesGeometry {
  const bark = lin(0x5e4733);
  const dark = lin(0x35592a);
  const light = lin(0x7aa64c);
  const make = (detail: number, lobes: number) => {
    const rnd = mulberry32(131);
    const trunk = new CylinderGeometry(0.03, 0.05, 0.5, 5, 1);
    trunk.translate(0, 0.25, 0);
    const parts: BufferGeometry[] = [colorize(trunk, (_p, _n, c) => c.copy(bark))];
    for (let i = 0; i < lobes; i++) {
      const r = lobes > 2 ? 0.17 + rnd() * 0.1 : 0.3;
      const blob = new IcosahedronGeometry(r, detail);
      const spread = lobes > 2 ? 0.28 : 0.08;
      blob.translate((rnd() - 0.5) * spread, 0.62 + rnd() * 0.18, (rnd() - 0.5) * spread);
      parts.push(colorize(blob, (_p, n, c) => c.copy(dark).lerp(light, 0.3 + 0.5 * Math.max(0, n.y))));
    }
    return merge(parts);
  };
  return { lod0: make(1, 5), lod1: make(0, 2) };
}
