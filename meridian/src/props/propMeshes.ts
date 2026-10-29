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

// ------------------------------------------------- appended species (studio)

/** Loam vesicle (Ilex): a low cluster of translucent teal bladders on the grove floor. Height ~1. */
export function loamVesicle(): SpeciesGeometry {
  const deep = lin(0x1f4a44);
  const pale = lin(0x9fd8c4);
  const stalk = lin(0x4a3d30);
  const make = (detail: boolean) => {
    const rnd = mulberry32(81);
    const parts: BufferGeometry[] = [];
    for (let i = 0; i < 6; i++) {
      const r = 0.16 + rnd() * 0.16;
      const a = rnd() * Math.PI * 2;
      const d = i === 0 ? 0 : 0.18 + rnd() * 0.25;
      const s = new SphereGeometry(r, detail ? 8 : 5, detail ? 6 : 3);
      s.scale(1, 1.25, 1);
      s.translate(Math.cos(a) * d, r * 1.1 + (i === 0 ? 0.35 : rnd() * 0.15), Math.sin(a) * d);
      parts.push(colorize(s, (p, n, c) => c.copy(deep).lerp(pale, Math.min(1, 0.25 + Math.max(0, n.y) * 0.6 + p.y * 0.3))));
      if (detail) {
        const st = new CylinderGeometry(0.012, 0.02, r * 1.2, 3, 1, true);
        st.translate(Math.cos(a) * d, r * 0.6, Math.sin(a) * d);
        parts.push(colorize(st, (_p, _n, c) => c.copy(stalk)));
      }
    }
    return merge(parts);
  };
  return { lod0: make(true), lod1: make(false) };
}

/** Fulgurite tube (Vesper): branching hollow glass tubes fused from sand. Height ~1. */
export function fulgurite(): SpeciesGeometry {
  const sand = lin(0xc2a57d);
  const glass = lin(0x5a5048);
  const make = (sides: number, branches: number) => {
    const rnd = mulberry32(91);
    const parts: BufferGeometry[] = [];
    const trunk = new CylinderGeometry(0.05, 0.08, 1, sides, 3, true);
    trunk.translate(0, 0.5, 0);
    trunk.rotateZ(0.12);
    parts.push(trunk);
    for (let i = 0; i < branches; i++) {
      const l = 0.3 + rnd() * 0.35;
      const b = new CylinderGeometry(0.02, 0.045, l, sides, 1, true);
      b.translate(0, l / 2, 0);
      b.rotateZ((rnd() - 0.5) * 1.6);
      b.rotateY(rnd() * Math.PI * 2);
      b.translate(0, 0.15 + rnd() * 0.5, 0);
      parts.push(b);
    }
    const g = merge(parts);
    return colorize(g, (p, n, c) => c.copy(glass).lerp(sand, Math.min(1, 0.4 + 0.5 * Math.abs(n.y) + 0.2 * Math.sin(p.y * 30))));
  };
  return { lod0: make(6, 5), lod1: make(3, 2) };
}

/** Frost bloom (Cairn): feathered hoar plates fanning out from a rock face. Height ~1. */
export function frostBloom(): SpeciesGeometry {
  const deep = lin(0x8fb6dd);
  const pale = lin(0xf0f7ff);
  const make = (count: number) => {
    const rnd = mulberry32(101);
    const parts: BufferGeometry[] = [];
    for (let i = 0; i < count; i++) {
      // A thin fan blade: a flattened cone, tilted outward.
      const h = 0.5 + rnd() * 0.5;
      const f = new ConeGeometry(0.22 + rnd() * 0.1, h, 4, 1);
      f.scale(1, 1, 0.12);
      f.translate(0, h / 2, 0);
      f.rotateX((rnd() - 0.5) * 1.1);
      f.rotateY(rnd() * Math.PI * 2);
      parts.push(f);
    }
    const g = merge(parts);
    return colorize(g, (p, n, c) => c.copy(deep).lerp(pale, Math.min(1, 0.3 + p.y * 0.7 + Math.abs(n.y) * 0.2)));
  };
  return { lod0: make(9), lod1: make(4) };
}

// ----------------------------------------------------------------- Orrin

/** Violet cushion-moss: a low mound of soft lobes. Height ~1 (scaled small). */
export function cushionMoss(): SpeciesGeometry {
  const deep = lin(0x4a3a60);
  const bright = lin(0x8a6ea4);
  const make = (detail: boolean) => {
    const rnd = mulberry32(111);
    const parts: BufferGeometry[] = [];
    for (let i = 0; i < 5; i++) {
      const r = 0.35 + rnd() * 0.3;
      const s = new SphereGeometry(r, detail ? 9 : 5, detail ? 5 : 3, 0, Math.PI * 2, 0, Math.PI / 2);
      s.scale(1, 1.4, 1);
      s.translate((rnd() - 0.5) * 0.9, 0, (rnd() - 0.5) * 0.9);
      parts.push(s);
    }
    return colorize(merge(parts), (p, n, c) => c.copy(deep).lerp(bright, Math.min(1, Math.max(0, n.y) * 0.7 + p.y * 0.4)));
  };
  return { lod0: make(true), lod1: make(false) };
}

/** Basalt organ: a cluster of hexagonal columns of different heights. Height 1. */
export function basaltOrgan(): SpeciesGeometry {
  const dark = lin(0x2a2930);
  const face = lin(0x3e3c46);
  const top = lin(0x5c5468);
  const make = (count: number) => {
    const rnd = mulberry32(121);
    const parts: BufferGeometry[] = [];
    for (let i = 0; i < count; i++) {
      const h = 0.45 + rnd() * 0.55;
      const c = new CylinderGeometry(0.11, 0.11, h, 6, 1);
      c.translate((i % 3 - 1) * 0.2 + (Math.floor(i / 3) % 2) * 0.1, h / 2, (Math.floor(i / 3) - 1) * 0.18);
      parts.push(c);
    }
    return colorize(merge(parts), (p, n, c) => (n.y > 0.9 ? c.copy(top) : c.copy(dark).lerp(face, 0.5 + 0.5 * Math.sin(p.y * 20))));
  };
  return { lod0: make(9), lod1: make(5) };
}

/** Fog reed: tall, hollow, slightly bent stems with pale seed heads. Height ~1. */
export function fogReed(): SpeciesGeometry {
  const stem = lin(0x5e6a68);
  const head = lin(0xc8ccd0);
  const make = (count: number, sides: number) => {
    const rnd = mulberry32(131);
    const parts: BufferGeometry[] = [];
    for (let i = 0; i < count; i++) {
      const h = 0.7 + rnd() * 0.3;
      const c = new CylinderGeometry(0.008, 0.016, h, sides, 2, true);
      c.translate(0, h / 2, 0);
      c.rotateZ((rnd() - 0.5) * 0.25);
      c.translate((rnd() - 0.5) * 0.3, 0, (rnd() - 0.5) * 0.3);
      parts.push(c);
      const s = new SphereGeometry(0.03, sides + 1, 3);
      s.scale(1, 2.5, 1);
      s.translate((rnd() - 0.5) * 0.05, h, 0);
      parts.push(s);
    }
    return colorize(merge(parts), (p, _n, c) => c.copy(stem).lerp(head, Math.max(0, p.y - 0.65) * 3));
  };
  return { lod0: make(9, 4), lod1: make(5, 3) };
}

/** Lamp cap: a few stalked caps with dim violet glowing undersides. Height ~1. */
export function lampCap(): SpeciesGeometry {
  const stalk = lin(0xb8b0c4);
  const cap = lin(0x4a3a60);
  const glow = lin(0xc7a6ff);
  const make = (detail: boolean) => {
    const rnd = mulberry32(141);
    const parts: BufferGeometry[] = [];
    for (let i = 0; i < 4; i++) {
      const h = 0.4 + rnd() * 0.5;
      const x = (rnd() - 0.5) * 0.5;
      const z = (rnd() - 0.5) * 0.5;
      const st = new CylinderGeometry(0.03, 0.045, h, detail ? 6 : 3, 1);
      st.translate(x, h / 2, z);
      parts.push(st);
      const r = 0.12 + rnd() * 0.1;
      const c = new SphereGeometry(r, detail ? 10 : 5, detail ? 5 : 3, 0, Math.PI * 2, 0, Math.PI / 2);
      c.scale(1, 0.5, 1);
      c.translate(x, h, z);
      parts.push(c);
    }
    return colorize(merge(parts), (p, n, c) => {
      if (n.y < -0.3) c.copy(glow);
      else if (p.y > 0.35 && n.y > 0.2) c.copy(cap);
      else c.copy(stalk);
    });
  };
  return { lod0: make(true), lod1: make(false) };
}

// ------------------------------------------------------------------ Saro

/** Halite rosette: a cluster of pink cubic salt crystals. Height ~1. */
export function haliteRosette(): SpeciesGeometry {
  const pink = lin(0xe6c3c0);
  const pale = lin(0xfaf0ec);
  const make = (count: number) => {
    const rnd = mulberry32(151);
    const parts: BufferGeometry[] = [];
    for (let i = 0; i < count; i++) {
      const s = 0.18 + rnd() * 0.3;
      const b = new CylinderGeometry(s * 0.7, s * 0.7, s, 4, 1);
      b.rotateY(Math.PI / 4 + rnd());
      b.rotateX((rnd() - 0.5) * 0.8);
      b.translate((rnd() - 0.5) * 0.6, s * 0.4 + rnd() * 0.2, (rnd() - 0.5) * 0.6);
      parts.push(b);
    }
    return colorize(merge(parts), (_p, n, c) => c.copy(pink).lerp(pale, Math.max(0, n.y) * 0.8));
  };
  return { lod0: make(8), lod1: make(4) };
}

/** Salt chimney: a hollow, tapering brine-fed tube ringed with crust. Height 1. */
export function saltChimney(): SpeciesGeometry {
  const crust = lin(0xf3e1da);
  const ring = lin(0xcf9fa0);
  const wet = lin(0x5cc4bc);
  const make = (radial: number) => {
    const c = new CylinderGeometry(0.09, 0.22, 1, radial, 6, true);
    const p = c.attributes.position;
    for (let i = 0; i < p.count; i++) {
      const y = p.getY(i) + 0.5;
      const k = 1 + 0.12 * Math.sin(y * 28);
      p.setX(i, p.getX(i) * k);
      p.setZ(i, p.getZ(i) * k);
    }
    c.translate(0, 0.5, 0);
    const lip = new CylinderGeometry(0.1, 0.07, 0.04, radial, 1, true);
    lip.translate(0, 1, 0);
    return colorize(merge([c, lip]), (q, _n, col) => (q.y > 0.97 ? col.copy(wet) : col.copy(crust).lerp(ring, 0.5 + 0.5 * Math.sin(q.y * 28))));
  };
  return { lod0: make(10), lod1: make(5) };
}

/** Brine mat: a flat, layered microbial mat in the shallows (orange to crimson rings). Height ~1 = width. */
export function brineMat(): SpeciesGeometry {
  const outer = lin(0xd8743a);
  const inner = lin(0x8a2030);
  const make = (segments: number) => {
    const rnd = mulberry32(161);
    const parts: BufferGeometry[] = [];
    for (let i = 0; i < 3; i++) {
      const r = 0.5 - i * 0.14;
      const d = new CylinderGeometry(r, r * 1.05, 0.02, segments, 1);
      d.translate((rnd() - 0.5) * 0.1, 0.01 + i * 0.012, (rnd() - 0.5) * 0.1);
      parts.push(d);
    }
    return colorize(merge(parts), (p, _n, c) => c.copy(outer).lerp(inner, Math.min(1, p.y * 30)));
  };
  return { lod0: make(16), lod1: make(7) };
}

/** Crust thorn: sparse pale halophyte spikes along the crack lines. Height ~1. */
export function crustThorn(): SpeciesGeometry {
  const base = lin(0xa88a8a);
  const tip = lin(0xf3e1da);
  const rnd = mulberry32(171);
  const parts: BufferGeometry[] = [];
  for (let i = 0; i < 6; i++) {
    const h = 0.6 + rnd() * 0.4;
    const c = new ConeGeometry(0.03, h, 4, 1);
    c.translate(0, h / 2, 0);
    c.rotateZ((rnd() - 0.5) * 0.7);
    c.rotateX((rnd() - 0.5) * 0.7);
    c.translate((rnd() - 0.5) * 0.2, 0, (rnd() - 0.5) * 0.2);
    parts.push(c);
  }
  const g = merge(parts);
  colorize(g, (p, _n, c) => c.copy(base).lerp(tip, Math.min(1, p.y)));
  return { lod0: g, lod1: null };
}

/** Sublimation vent (Cairn): a dark fissure in the crater floor inside a ring of fresh frost. Height ~1 = width. */
export function sublimationVent(): SpeciesGeometry {
  const frost = lin(0xe6f2ff);
  const rock = lin(0x4b4d52);
  const dark = lin(0x15161a);
  const make = (segments: number) => {
    const rnd = mulberry32(181);
    const ring = new CylinderGeometry(0.5, 0.56, 0.05, segments, 1);
    const rp = ring.attributes.position;
    for (let i = 0; i < rp.count; i++) {
      const k = 1 + (rnd() - 0.5) * 0.25;
      rp.setX(i, rp.getX(i) * k);
      rp.setZ(i, rp.getZ(i) * k);
    }
    ring.translate(0, 0.02, 0);
    const lips: BufferGeometry[] = [];
    for (const sx of [1, -1]) {
      const l = new CylinderGeometry(0.05, 0.08, 0.7, 4, 1);
      l.rotateZ(Math.PI / 2);
      l.scale(1, 0.6, 1);
      l.translate(0, 0.07, sx * 0.07);
      lips.push(l);
    }
    const g = merge([ring, ...lips]);
    return colorize(g, (p, _n, c) => {
      const r = Math.hypot(p.x, p.z);
      if (Math.abs(p.z) < 0.04 && Math.abs(p.x) < 0.35) c.copy(dark);
      else if (p.y > 0.06) c.copy(rock);
      else c.copy(rock).lerp(frost, Math.min(1, 1.6 - r * 2.2));
    });
  };
  return { lod0: make(14), lod1: make(6) };
}
