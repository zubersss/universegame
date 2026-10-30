// Deterministic, pure surface definition shared by the terrain worker and the
// main thread:  surface(n) = center + n * (radius + height(n)).
// Noise is evaluated in continuous 3D planet coordinates (p = n * R), so the
// six cube faces agree everywhere. Height paths use only IEEE arithmetic,
// Math.floor, Math.sqrt and seeded simplex noise (no Math.random, no time).

import { createNoise3D, type NoiseFunction3D } from 'simplex-noise';
import { hashCombine, mulberry32 } from '../core/rng';
import type { BodyDef } from './bodies';
import { earthData, latLonOf, loadEarthData, sampleBilinear, type EarthRasters } from './earthData';
import { ELEVATION_DIVISOR } from './scale';

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
  /** Environmental hazard 0..1 (heat, cold, pressure, liquid). Always written by the generators. */
  hazard?: number;
  /** Height above the datum [m] of the liquid surface covering this point, null where dry. Always written by the generators. */
  liquidLevel?: number | null;
}

/** A SurfaceInfo with every field set (use for scratch objects). */
export function newSurfaceInfo(): SurfaceInfo {
  return { height: 0, biome: 0, variation: 0, special: 0, rockiness: 0, hazard: 0, liquidLevel: null };
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

/** Polynomial smooth minimum (C1), k > 0 is the blend width; smin(a, b, k) <= min(a, b). */
function smin(a: number, b: number, k: number): number {
  if (k <= 0) return a < b ? a : b;
  const h = Math.max(k - Math.abs(a - b), 0) / k;
  return Math.min(a, b) - h * h * k * 0.25;
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
  private readonly earthRasters: EarthRasters | null = null;

  constructor(readonly def: BodyDef) {
    this.R = def.radius;
    this.maxHeight = def.maxHeight;
    if (def.surface === 'data') {
      if (def.dataset !== 'earth') throw new Error(`Unknown dataset ${def.dataset} for ${def.id}`);
      this.earthRasters = earthData();
      if (!this.earthRasters) throw new Error(`${def.id}: surface data not loaded (await ensureBodyData(def) first)`);
    }
    const names = ['w1', 'w2', 'w3', 'c', 'm', 'r', 'h', 'd', 'v', 'g', 'rg', 'rg2', 'ms', 'du', 'da', 'db', 'o', 'b', 'b2', 'ba'];
    for (const k of names) this.n[k] = makeNoise(def.seed, k);
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
    out.hazard = 0;
    out.liquidLevel = null;
    if (this.earthRasters) return this.earth(nx, ny, nz, out);
    switch (this.def.id) {
      case 'ilex':
        return this.ilex(nx, ny, nz, out);
      case 'vesper':
        return this.vesper(nx, ny, nz, out);
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

  private readonly scratch: SurfaceInfo = newSurfaceInfo();

  /** Final height (with clearings). */
  height(nx: number, ny: number, nz: number): number {
    return this.info(nx, ny, nz, this.scratch).height;
  }

  // --------------------------------------------------------------- Earth
  // Real data (elevation, coastline distance, water level, land cover) sampled
  // bilinearly in the body's latitude/longitude frame; procedural infill below
  // the data resolution is keyed by the seed. Shaping keeps every point's
  // land/water sign equal to the coastline data, so no seed moves a coast.
  // Work is in real metres, converted to gameplay height at the end.

  private readonly ll = { lat: 0, lon: 0 };

  private earth(nx: number, ny: number, nz: number, out: SurfaceInfo): SurfaceInfo {
    const ed = this.earthRasters!;
    const f = this.def.frame;
    const n = this.n;
    const R = this.R;
    const ll = latLonOf(nx, ny, nz, f.north, f.meridian, f.east, this.ll);
    const lat = ll.lat;
    const lon = ll.lon;
    const e = sampleBilinear(ed.elevation, lat, lon); // m above mean sea level
    const d = sampleBilinear(ed.coast, lat, lon); // km to the nearest shore, + on land
    const W = sampleBilinear(ed.water, lat, lon); // m, surface level of the nearest water body (ocean 0)

    // Data relief: central differences over one elevation cell (continuous in position).
    const res = ed.elevation.res;
    const sinLat = nx * f.north[0] + ny * f.north[1] + nz * f.north[2];
    const cosLat = Math.max(Math.sqrt(Math.max(0, 1 - sinLat * sinLat)), 0.05);
    let lonE = lon + res;
    if (lonE > 180) lonE -= 360;
    let lonW = lon - res;
    if (lonW < -180) lonW += 360;
    const gx = (sampleBilinear(ed.elevation, lat, lonE) - sampleBilinear(ed.elevation, lat, lonW)) / (2 * res * 111.2 * cosLat);
    const gy = (sampleBilinear(ed.elevation, Math.min(90, lat + res), lon) - sampleBilinear(ed.elevation, Math.max(-90, lat - res), lon)) / (2 * res * 111.2);
    const slope = Math.sqrt(gx * gx + gy * gy); // m per km

    // Infill below the data resolution (noise in planet metres, gameplay scale).
    const px = nx * R;
    const py = ny * R;
    const pz = nz * R;
    const fw = 1 / 6000;
    const qx = px + 500 * n.w1(px * fw, py * fw, pz * fw);
    const qy = py + 500 * n.w2(px * fw, py * fw, pz * fw);
    const qz = pz + 500 * n.w3(px * fw, py * fw, pz * fw);
    const mount = sstep(12, 60, slope);
    const amp = Math.min(30 + 6 * slope + 0.12 * Math.max(e - W, 0), 2200);
    const rid = ridged(n.r, qx / 2600, qy / 2600, qz / 2600, 3);
    const hil = fbm(n.h, qx / 1700, qy / 1700, qz / 1700, 2);
    const det = fbm(n.d, px / 140, py / 140, pz / 140, 3);
    let h = e + amp * (mount * (rid - 0.4) * 1.6 + (1 - mount) * hil * 0.5) + det * (4 + 30 * mount);

    // Shore shaping: land rises from the water level W, water sinks below it;
    // the bounds meet at the shoreline (d = 0), so h - W has the sign of d.
    const a = d < 0 ? -d : d;
    const ramp = 4 * (a / 0.6) / (1 + a / 0.6); // 0 at the shore, 4 m inland / below
    const a8 = (a / 8) * (a / 8);
    const lift = W / (1 + a8 * a8); // nearest water level, fading beyond ~10 km
    const room = 10 * a * a; // freedom away from the shore (m)
    const k = Math.min(20, 6 * a, 2 * ramp); // blend width: keeps h - W strictly signed near the shore
    if (d >= 0) {
      const lo = lift + ramp;
      h = smin(-smin(-h, -lo, k), lo + room, k);
    } else {
      const hi = W - ramp;
      h = smin(-smin(-h, -(hi - room), k), hi, k);
      // Deep water compressed (rational, so deterministic): at most ~1.5 km below the surface.
      const top = W - 200;
      if (h < top) {
        const u = (top - h) / 1300;
        h = top - (1300 * u) / (1 + u);
      }
    }

    const sea = this.def.seaLevel ?? 0;
    out.height = sea + h / ELEVATION_DIVISOR;
    out.liquidLevel = d < 0 ? sea + W / ELEVATION_DIVISOR : null;

    // Land cover (normalized fractions; coastal cells mix in empty ocean cells).
    const b = ed.biome;
    const tree = sampleBilinear(b, lat, lon, 0);
    const low = sampleBilinear(b, lat, lon, 1);
    const bare = sampleBilinear(b, lat, lon, 2);
    const ice = sampleBilinear(b, lat, lon, 3);
    const tun = sampleBilinear(b, lat, lon, 4);
    const sum = tree + low + bare + ice + tun;
    const inv = sum > 0.05 ? 1 / sum : 0;
    const veg = (tree + low) * inv;
    const treeShare = tree * inv;
    const iceShare = ice * inv;
    // Snow above a latitude-dependent line (real metres), on top of mapped ice.
    const snowLine = 5200 - 5600 * (lat / 75) * (lat / 75);
    const snow = sstep(snowLine - 300, snowLine + 500, h);
    out.biome = d < 0 ? 0 : sum > 0.05 ? veg : 0.3;
    out.variation = sat(0.3 + 0.55 * treeShare + 0.2 * n.v(px / 3000, py / 3000, pz / 3000));
    out.special = d < 0 ? 0 : Math.max(iceShare, snow);
    out.rockiness = d < 0 ? 0.1 : sat(mount * (0.35 + 0.6 * (bare + tun * 0.5) * inv) + 0.25 * (1 - veg) * mount);
    return out;
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
}

/** True when a body's surface can be generated in this thread (its dataset, if any, is loaded). */
export function bodyDataReady(def: BodyDef): boolean {
  return def.surface !== 'data' || earthData() !== null;
}

/**
 * Load a body's surface dataset in this thread (no-op for procedural bodies).
 * Await it before constructing a SurfaceGenerator, computeSites or an
 * ActiveBody for a 'data' body; the terrain worker does this by itself.
 */
export function ensureBodyData(def: BodyDef): Promise<void> {
  if (def.surface !== 'data') return Promise.resolve();
  return loadEarthData().then(() => undefined);
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
