// Deterministic, pure surface definition shared by the terrain worker and the
// main thread:  surface(n) = center + n * (radius + height(n)).
// Noise is evaluated in continuous 3D planet coordinates (p = n * R), so the
// six cube faces agree everywhere. Height paths use only IEEE arithmetic,
// Math.floor, Math.sqrt and seeded simplex noise (no Math.random, no time).

import { createNoise3D, type NoiseFunction3D } from 'simplex-noise';
import { hashCombine, mulberry32 } from '../core/rng';
import type { BodyDef } from './bodies';

export interface SurfaceInfo {
  height: number;
  /** 0 = biome A, 1 = biome B. */
  biome: number;
  /** Low-frequency color variation 0..1. */
  variation: number;
  /** Deposit / special material mask 0..1 (grove soil, black mineral, ice). */
  special: number;
  /** Tendency to expose bare rock independent of slope 0..1. */
  rockiness: number;
}

/** A flattened clearing blended into the height field (landing sites, relay pads). */
export interface Clearing {
  dir: [number, number, number];
  height: number;
  r0: number;
  r1: number;
}

const sat = (x: number) => (x < 0 ? 0 : x > 1 ? 1 : x);
const sstep = (e0: number, e1: number, x: number) => {
  const t = sat((x - e0) / (e1 - e0));
  return t * t * (3 - 2 * t);
};

function makeNoise(seed: number, name: string): NoiseFunction3D {
  return createNoise3D(mulberry32(hashCombine(seed, name)));
}

/** Fractal sum normalized to roughly [-1, 1]. */
function fbm(n: NoiseFunction3D, x: number, y: number, z: number, oct: number): number {
  let sum = 0;
  let amp = 1;
  let norm = 0;
  let f = 1;
  for (let i = 0; i < oct; i++) {
    sum += n(x * f, y * f, z * f) * amp;
    norm += amp;
    amp *= 0.5;
    f *= 2.03;
  }
  return sum / norm;
}

/** Ridged multifractal in [0, 1]: sharp crests where noise crosses zero. */
function ridged(n: NoiseFunction3D, x: number, y: number, z: number, oct: number): number {
  let sum = 0;
  let amp = 1;
  let norm = 0;
  let f = 1;
  let w = 1;
  for (let i = 0; i < oct; i++) {
    let s = 1 - Math.abs(n(x * f, y * f, z * f));
    s *= s;
    s *= w;
    w = sat(s * 1.6);
    sum += s * amp;
    norm += amp;
    amp *= 0.5;
    f *= 2.07;
  }
  return sum / norm;
}

/** Fast deterministic hash of three integers + salt to [0, 1). */
function h3(x: number, y: number, z: number, salt: number): number {
  let h = Math.imul(x | 0, 0x8da6b343) ^ Math.imul(y | 0, 0xd8163841) ^ Math.imul(z | 0, 0xcb1ab31f) ^ salt;
  h = Math.imul(h ^ (h >>> 15), 0x2c1b3c6d);
  h = Math.imul(h ^ (h >>> 12), 0x297a2d39);
  h ^= h >>> 15;
  return (h >>> 0) / 4294967296;
}

interface CraterScale {
  cell: number;
  rMin: number;
  rMax: number;
  prob: number;
  depth: number;
  depthCap: number;
  salt: number;
}

export class SurfaceGenerator {
  readonly R: number;
  readonly maxHeight: number;
  private readonly n: Record<string, NoiseFunction3D> = {};
  clearings: Clearing[] = [];
  private readonly craterScales: CraterScale[] = [];
  private readonly windAxis: [number, number, number] = [0.83, 0.18, 0.53];
  /** Hash salt for per-cell features (basalt columns, salt polygons). */
  private readonly cellSalt: number;

  constructor(readonly def: BodyDef) {
    this.R = def.radius;
    this.maxHeight = def.maxHeight;
    const names = ['w1', 'w2', 'w3', 'c', 'm', 'r', 'h', 'd', 'v', 'g', 'rg', 'rg2', 'ms', 'du', 'da', 'db', 'o', 'b', 'b2', 'ba'];
    for (const k of names) this.n[k] = makeNoise(def.seed, k);
    this.cellSalt = hashCombine(def.seed, 'cells') | 0;
    if (def.id === 'cairn') {
      const s = def.seed;
      // Radial projection moves a crater center by up to cell/2, so a crater from
      // outside the 27-cell neighborhood can be as close as cell/2: influence
      // (1.45 r) must stay below cell/2, i.e. rMax <= 0.345 * cell.
      this.craterScales.push(
        { cell: 3200, rMin: 380, rMax: 1050, prob: 0.5, depth: 0.15, depthCap: 150, salt: hashCombine(s, 'cr1') | 0 },
        { cell: 900, rMin: 90, rMax: 300, prob: 0.55, depth: 0.19, depthCap: 60, salt: hashCombine(s, 'cr2') | 0 },
        { cell: 260, rMin: 18, rMax: 85, prob: 0.5, depth: 0.2, depthCap: 16, salt: hashCombine(s, 'cr3') | 0 },
      );
    }
  }

  /** Height without mission clearings (used for site selection). */
  baseInfo(nx: number, ny: number, nz: number, out: SurfaceInfo): SurfaceInfo {
    switch (this.def.id) {
      case 'ilex':
        return this.ilex(nx, ny, nz, out);
      case 'vesper':
        return this.vesper(nx, ny, nz, out);
      case 'orrin':
        return this.orrin(nx, ny, nz, out);
      case 'saro':
        return this.saro(nx, ny, nz, out);
      default:
        return this.cairn(nx, ny, nz, out);
    }
  }

  /** Final surface info including clearings, height clamped to [0, maxHeight]. */
  info(nx: number, ny: number, nz: number, out: SurfaceInfo): SurfaceInfo {
    this.baseInfo(nx, ny, nz, out);
    for (let i = 0; i < this.clearings.length; i++) {
      const c = this.clearings[i];
      const dx = nx - c.dir[0];
      const dy = ny - c.dir[1];
      const dz = nz - c.dir[2];
      const d = Math.sqrt(dx * dx + dy * dy + dz * dz) * this.R;
      if (d < c.r1) {
        const w = 1 - sstep(c.r0, c.r1, d);
        out.height = out.height + (c.height - out.height) * w;
        out.rockiness *= 1 - w;
      }
    }
    out.height = out.height < 0 ? 0 : out.height > this.maxHeight ? this.maxHeight : out.height;
    return out;
  }

  private readonly scratch: SurfaceInfo = { height: 0, biome: 0, variation: 0, special: 0, rockiness: 0 };

  /** Final height (with clearings). */
  height(nx: number, ny: number, nz: number): number {
    return this.info(nx, ny, nz, this.scratch).height;
  }

  // ---------------------------------------------------------------- Ilex

  private ilex(nx: number, ny: number, nz: number, out: SurfaceInfo): SurfaceInfo {
    const n = this.n;
    const R = this.R;
    const px = nx * R;
    const py = ny * R;
    const pz = nz * R;
    const fw = 1 / 6000;
    const qx = px + 600 * n.w1(px * fw, py * fw, pz * fw);
    const qy = py + 600 * n.w2(px * fw, py * fw, pz * fw);
    const qz = pz + 600 * n.w3(px * fw, py * fw, pz * fw);
    const continent = fbm(n.c, qx / 16000, qy / 16000, qz / 16000, 3);
    const moisture = n.m(px / 11000, py / 11000, pz / 11000);
    const highland = sstep(-0.12, 0.28, continent * 0.85 + moisture * 0.35);
    const ridges = ridged(n.r, qx / 2600, qy / 2600, qz / 2600, 3);
    const hills = fbm(n.h, qx / 1700, qy / 1700, qz / 1700, 2);
    const detail = fbm(n.d, px / 140, py / 140, pz / 140, 3);
    const base = 120 + 110 * continent;
    const hi = 70 + 560 * ridges * ridges * (0.55 + 0.45 * ridges);
    const lo = 25 + 40 * (hills * 0.5 + 0.5);
    out.height = base + highland * hi + (1 - highland) * lo + detail * (3 + 5 * highland);
    out.biome = 1 - highland;
    out.variation = 0.5 + 0.5 * n.v(px / 3000, py / 3000, pz / 3000);
    out.special = sstep(0.05, 0.45, n.g(px / 900, py / 900, pz / 900)) * sat((1 - highland) * 1.4);
    out.rockiness = highland * sstep(0.32, 0.68, ridges);
    return out;
  }

  // -------------------------------------------------------------- Vesper

  private vesper(nx: number, ny: number, nz: number, out: SurfaceInfo): SurfaceInfo {
    const n = this.n;
    const R = this.R;
    const px = nx * R;
    const py = ny * R;
    const pz = nz * R;
    const fw = 1 / 5000;
    const qx = px + 400 * n.w1(px * fw, py * fw, pz * fw);
    const qy = py + 400 * n.w2(px * fw, py * fw, pz * fw);
    const qz = pz + 400 * n.w3(px * fw, py * fw, pz * fw);
    const region = n.rg(px / 14000, py / 14000, pz / 14000) + 0.5 * n.rg2(px / 6000, py / 6000, pz / 6000);
    const mesaW = sstep(-0.05, 0.3, region);
    // Terraced mesas: flat treads with steep risers and a few tall plateaus.
    const m = 0.5 + 0.5 * fbm(n.ms, qx / 4200, qy / 4200, qz / 4200, 3);
    const tv = m * 6;
    const fl = Math.floor(tv);
    const terr = fl + sstep(0.78, 0.96, tv - fl);
    const mesaH = 60 + terr * 112 + sstep(0.62, 0.665, m) * 170;
    // Dunes: asymmetric ridges across a wind axis, phase-warped by noise.
    const a = this.windAxis;
    const s = (qx * a[0] + qy * a[1] + qz * a[2]) / 330 + 0.35 * n.du(qx / 2500, qy / 2500, qz / 2500);
    const ph = s - Math.floor(s);
    const prof = ph < 0.72 ? sstep(0, 0.72, ph) : 1 - sstep(0.72, 1, ph);
    const duneAmp = 16 + 22 * (0.5 + 0.5 * n.da(px / 5000, py / 5000, pz / 5000));
    const duneH = 70 + prof * duneAmp + 38 * (0.5 + 0.5 * fbm(n.db, qx / 3000, qy / 3000, qz / 3000, 2));
    const detail = fbm(n.d, px / 140, py / 140, pz / 140, 3);
    out.height = duneH + (mesaH - duneH) * mesaW + detail * (2 + 2 * mesaW);
    out.biome = 1 - mesaW;
    out.variation = 0.5 + 0.5 * n.v(px / 2600, py / 2600, pz / 2600);
    out.special = sstep(0.5, 0.78, n.o(px / 420, py / 420, pz / 420));
    out.rockiness = mesaW * 0.55;
    return out;
  }

  // --------------------------------------------------------------- Cairn

  private cairn(nx: number, ny: number, nz: number, out: SurfaceInfo): SurfaceInfo {
    const n = this.n;
    const R = this.R;
    const px = nx * R;
    const py = ny * R;
    const pz = nz * R;
    const basin = sstep(0.0, 0.35, n.ba(px / 7000, py / 7000, pz / 7000));
    let h = 270 + 110 * fbm(n.b, px / 5200, py / 5200, pz / 5200, 3) + 22 * fbm(n.b2, px / 900, py / 900, pz / 900, 2);
    h -= 120 * basin;
    let floorness = 0;
    for (let si = 0; si < this.craterScales.length; si++) {
      const sc = this.craterScales[si];
      const S = sc.cell;
      const cx = Math.floor(px / S);
      const cy = Math.floor(py / S);
      const cz = Math.floor(pz / S);
      for (let dz = -1; dz <= 1; dz++) {
        for (let dy = -1; dy <= 1; dy++) {
          for (let dx = -1; dx <= 1; dx++) {
            const ix = cx + dx;
            const iy = cy + dy;
            const iz = cz + dz;
            if (h3(ix, iy, iz, sc.salt) >= sc.prob) continue;
            const jx = (ix + h3(ix, iy, iz, sc.salt + 1)) * S;
            const jy = (iy + h3(ix, iy, iz, sc.salt + 2)) * S;
            const jz = (iz + h3(ix, iy, iz, sc.salt + 3)) * S;
            const jl = Math.sqrt(jx * jx + jy * jy + jz * jz);
            // Only cells whose jittered point lies near the surface spawn craters (uniform density).
            if (Math.abs(jl - R) > S * 0.5) continue;
            const k = R / jl;
            const ex = px - jx * k;
            const ey = py - jy * k;
            const ez = pz - jz * k;
            const d = Math.sqrt(ex * ex + ey * ey + ez * ez);
            const r = sc.rMin + (sc.rMax - sc.rMin) * h3(ix, iy, iz, sc.salt + 4);
            const x = d / r;
            if (x >= 1.45) continue;
            const depth = Math.min(r * sc.depth, sc.depthCap);
            let c = 0;
            if (x < 1) {
              c = Math.max((x * x - 1) * depth, -depth * 0.82);
              const f = 1 - x;
              if (f > floorness) floorness = f;
            }
            const t = (x - 1) / 0.42;
            if (t > -1 && t < 1) {
              const b = 1 - t * t;
              c += depth * 0.24 * b * b;
            }
            h += c;
          }
        }
      }
    }
    const detail = fbm(n.d, px / 140, py / 140, pz / 140, 3);
    out.height = h + detail * 2.5;
    out.biome = basin;
    out.variation = 0.5 + 0.5 * n.v(px / 2200, py / 2200, pz / 2200);
    out.special = sat(basin * 1.3) * sstep(0.08, 0.5, floorness + 0.25 * basin);
    out.rockiness = (1 - basin) * 0.35;
    return out;
  }

  // --------------------------------------------------------------- Orrin

  private orrin(nx: number, ny: number, nz: number, out: SurfaceInfo): SurfaceInfo {
    const n = this.n;
    const R = this.R;
    const px = nx * R;
    const py = ny * R;
    const pz = nz * R;
    const fw = 1 / 5500;
    const qx = px + 500 * n.w1(px * fw, py * fw, pz * fw);
    const qy = py + 500 * n.w2(px * fw, py * fw, pz * fw);
    const qz = pz + 500 * n.w3(px * fw, py * fw, pz * fw);
    const region = fbm(n.c, qx / 15000, qy / 15000, qz / 15000, 3) + 0.4 * n.m(px / 7000, py / 7000, pz / 7000);
    const plateau = sstep(0.08, 0.32, region);
    // Lowlands: broad mossy swells cut by sinuous valleys (where the channel noise crosses zero).
    const swell = fbm(n.h, qx / 2200, qy / 2200, qz / 2200, 3);
    const ch = 1 - Math.abs(n.r(qx / 3800, qy / 3800, qz / 3800));
    const valley = sstep(0.8, 0.97, ch) * (1 - plateau);
    const lowH = 110 + 35 * swell - 55 * valley;
    // Highlands: a few stepped basalt treads with steep risers ...
    const m = 0.5 + 0.5 * fbm(n.ms, qx / 5200, qy / 5200, qz / 5200, 2);
    const tv = m * 4;
    const fl = Math.floor(tv);
    const terr = fl + sstep(0.85, 0.97, tv - fl);
    const highH = 190 + terr * 90;
    // ... broken into polygonal columns: 3D cells cut by the sphere, each raised by its own hash.
    const S = 30;
    const col = h3(Math.floor(px / S), Math.floor(py / S), Math.floor(pz / S), this.cellSalt) - 0.5;
    const colW = sstep(0.35, 0.8, plateau);
    const detail = fbm(n.d, px / 140, py / 140, pz / 140, 3);
    out.height = lowH + (highH - lowH) * plateau + col * 7 * colW + detail * (2 + 2 * plateau);
    out.biome = 1 - plateau;
    out.variation = 0.5 + 0.5 * n.v(px / 2800, py / 2800, pz / 2800);
    out.special = valley;
    out.rockiness = plateau * 0.8;
    return out;
  }

  // ---------------------------------------------------------------- Saro

  private saro(nx: number, ny: number, nz: number, out: SurfaceInfo): SurfaceInfo {
    const n = this.n;
    const R = this.R;
    const px = nx * R;
    const py = ny * R;
    const pz = nz * R;
    const fw = 1 / 4000;
    const qx = px + 300 * n.w1(px * fw, py * fw, pz * fw);
    const qy = py + 300 * n.w2(px * fw, py * fw, pz * fw);
    const qz = pz + 300 * n.w3(px * fw, py * fw, pz * fw);
    // Shallow brine pans in broad basins of an almost flat crust.
    const pan = sstep(0.15, 0.45, fbm(n.ba, qx / 9000, qy / 9000, qz / 9000, 3));
    const flats = 45 + 10 * fbm(n.b, qx / 6000, qy / 6000, qz / 6000, 2);
    // Scattered low salt domes.
    const domeW = sstep(0.3, 0.6, n.rg(px / 12000, py / 12000, pz / 12000));
    const dr = ridged(n.r, qx / 2400, qy / 2400, qz / 2400, 2);
    const domes = 70 * dr * dr * dr * domeW;
    // Polygonal pressure ridges along the edges of 3D Voronoi cells (F2 - F1 small).
    const S = 260;
    const cx = Math.floor(px / S);
    const cy = Math.floor(py / S);
    const cz = Math.floor(pz / S);
    let f1 = Infinity;
    let f2 = Infinity;
    for (let dz = -1; dz <= 1; dz++) {
      for (let dy = -1; dy <= 1; dy++) {
        for (let dx = -1; dx <= 1; dx++) {
          const ix = cx + dx;
          const iy = cy + dy;
          const iz = cz + dz;
          const ex = px - (ix + h3(ix, iy, iz, this.cellSalt + 1)) * S;
          const ey = py - (iy + h3(ix, iy, iz, this.cellSalt + 2)) * S;
          const ez = pz - (iz + h3(ix, iy, iz, this.cellSalt + 3)) * S;
          const d = ex * ex + ey * ey + ez * ez;
          if (d < f1) {
            f2 = f1;
            f1 = d;
          } else if (d < f2) f2 = d;
        }
      }
    }
    const edge = Math.sqrt(f2) - Math.sqrt(f1);
    const ridge = 1 - sstep(0, 22, edge);
    const detail = fbm(n.d, px / 140, py / 140, pz / 140, 2);
    out.height = flats + domes - 6 * pan + ridge * 2.2 * (1 - pan) + detail * 0.6;
    out.biome = pan;
    out.variation = 0.5 + 0.5 * n.v(px / 2400, py / 2400, pz / 2400);
    out.special = sstep(0.55, 0.85, pan);
    out.rockiness = domeW * dr * 0.5;
    return out;
  }
}

const generators = new Map<string, SurfaceGenerator>();

/** Shared (memoized) generator per body with its mission clearings installed. */
export function getSurface(def: BodyDef, clearings?: Clearing[]): SurfaceGenerator {
  let g = generators.get(def.id);
  if (!g) {
    g = new SurfaceGenerator(def);
    generators.set(def.id, g);
  }
  if (clearings) g.clearings = clearings;
  return g;
}
