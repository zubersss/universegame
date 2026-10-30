// Deterministic, pure surface definition shared by the terrain worker and the
// main thread:  surface(n) = center + n * (radius + height(n)).
// Noise is evaluated in continuous 3D planet coordinates (p = n * R), so the
// six cube faces agree everywhere. Height paths use only IEEE arithmetic,
// Math.floor, Math.sqrt and seeded simplex noise (no Math.random, no time).

import { createNoise3D, type NoiseFunction3D } from 'simplex-noise';
import { hashCombine, mulberry32 } from '../core/rng';
import type { BodyDef } from './bodies';
import { earthData, latLonOf, loadEarthData, sampleBilinear, sampleCubic, sampleElevation, type ElevationSample, type EarthRasters } from './earthData';
import { ELEVATION_DIVISOR } from './scale';
import { BODY_FEATURES, FeatureField } from './features';

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

/**
 * Share of a regional elevation grid's relief (above or below the global 10'
 * grid) kept on the gameplay surface. Heights are real / 5 over distances of
 * real / 40, so real alpine slopes would stand 8x steeper (needles); this keeps
 * the shapes (peaks, valleys, ridgelines) at climbable steepness (gameplay).
 */
export const EARTH_REGION_RELIEF = 0.35;
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

/** Crater probabilities per cell for the three size classes (large, medium, small), Sol bodies. */
const CRATER_DENSITY: Readonly<Record<string, [number, number, number]>> = {
  moon: [0.5, 0.55, 0.5],
  mercury: [0.55, 0.55, 0.5],
  mars: [0.3, 0.35, 0.35],
  venus: [0.04, 0.04, 0.02],
  europa: [0.05, 0.08, 0.08],
  titan: [0.03, 0.03, 0.02],
};

export class SurfaceGenerator {
  readonly R: number;
  readonly maxHeight: number;
  private readonly n: Record<string, NoiseFunction3D> = {};
  clearings: Clearing[] = [];
  private readonly craterScales: CraterScale[] = [];
  private readonly windAxis: [number, number, number] = [0.83, 0.18, 0.53];
  private readonly earthRasters: EarthRasters | null = null;
  /** Large real features (Mars, Moon) for the Sol procedural surfaces. */
  private readonly features: FeatureField | null = null;

  constructor(readonly def: BodyDef) {
    this.R = def.radius;
    this.maxHeight = def.maxHeight;
    const feats = BODY_FEATURES[def.id];
    if (feats) this.features = new FeatureField(def, feats);
    if (def.surface === 'data') {
      if (def.dataset !== 'earth') throw new Error(`Unknown dataset ${def.dataset} for ${def.id}`);
      this.earthRasters = earthData();
      if (!this.earthRasters) throw new Error(`${def.id}: surface data not loaded (await ensureBodyData(def) first)`);
    }
    const names = ['w1', 'w2', 'w3', 'c', 'm', 'r', 'h', 'd', 'v', 'g', 'rg', 'rg2', 'ms', 'du', 'da', 'db', 'o', 'b', 'b2', 'ba'];
    for (const k of names) this.n[k] = makeNoise(def.seed, k);
    const density = def.system === 'quiet' ? null : CRATER_DENSITY[def.id] ?? [0, 0, 0];
    if (density) {
      // Sol bodies: seeded crater infill below the data scale (sizes in gameplay metres), as on Cairn.
      const s = def.seed;
      this.craterScales.push(
        { cell: 3200, rMin: 380, rMax: 1050, prob: density[0], depth: 0.15, depthCap: 150, salt: hashCombine(s, 'cr1') | 0 },
        { cell: 900, rMin: 90, rMax: 300, prob: density[1], depth: 0.19, depthCap: 60, salt: hashCombine(s, 'cr2') | 0 },
        { cell: 260, rMin: 18, rMax: 85, prob: density[2], depth: 0.2, depthCap: 16, salt: hashCombine(s, 'cr3') | 0 },
      );
    }
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
    if (this.def.system !== 'quiet') return this.featured(nx, ny, nz, out);
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
  private readonly cs: ElevationSample = { v: 0, dLon: 0, dLat: 0, region: 0 };

  private earth(nx: number, ny: number, nz: number, out: SurfaceInfo): SurfaceInfo {
    const ed = this.earthRasters!;
    const f = this.def.frame;
    const n = this.n;
    const R = this.R;
    const ll = latLonOf(nx, ny, nz, f.north, f.meridian, f.east, this.ll);
    const lat = ll.lat;
    const lon = ll.lon;
    // Smooth (C2) fields for shape, so shading never shows raster cells; regional
    // high-resolution grids (the First Light Southern Alps) override the global one.
    const cs = sampleElevation(ed, lat, lon, this.cs, EARTH_REGION_RELIEF);
    const e = cs.v; // m above mean sea level
    const local = 1 - cs.region; // share of the coarse global grid
    const eData = cs.data ?? e; // regional relief uncompressed (for snow and ice)
    const sinLat = nx * f.north[0] + ny * f.north[1] + nz * f.north[2];
    const cosLat = Math.max(Math.sqrt(Math.max(0, 1 - sinLat * sinLat)), 0.05);
    const gx = cs.dLon / (111.2 * cosLat);
    const gy = cs.dLat / 111.2;
    // Data relief (m per km), faded to zero at the poles where its direction is undefined.
    const absLat = lat < 0 ? -lat : lat;
    const slope = Math.sqrt(gx * gx + gy * gy) * sstep(89.97, 89.6, absLat);
    const d = sampleCubic(ed.coast, lat, lon, this.cs).v; // km to the nearest shore, + on land
    const W = sampleBilinear(ed.water, lat, lon); // m, surface level of the nearest water body (ocean 0)

    // Infill below the data resolution (one elevation cell is 463 m of gameplay
    // surface): every seeded wavelength is at most a cell, so the seed adds
    // detail but does not reshape relief the data resolves. Noise runs in
    // planet metres (gameplay scale); amplitudes are real metres. Regional grids
    // resolve 8 m of gameplay surface, so there the infill shrinks to fine texture.
    const px = nx * R;
    const py = ny * R;
    const pz = nz * R;
    const fw = 1 / 1500;
    const qx = px + 120 * n.w1(px * fw, py * fw, pz * fw);
    const qy = py + 120 * n.w2(px * fw, py * fw, pz * fw);
    const qz = pz + 120 * n.w3(px * fw, py * fw, pz * fw);
    const mount = sstep(12, 60, slope);
    const amp = Math.min(25 + 4 * slope + 0.08 * Math.max(e - W, 0), 900) * local;
    const rid = ridged(n.r, qx / 460, qy / 460, qz / 460, 3);
    const hil = fbm(n.h, qx / 330, qy / 330, qz / 330, 2);
    const det = fbm(n.d, px / 140, py / 140, pz / 140, 3);
    let h = e + amp * (mount * (rid - 0.4) * 1.6 + (1 - mount) * hil * 0.5) + det * (4 + 24 * mount) * (0.2 + 0.8 * local);

    // Shore shaping: land rises from the water level W, water sinks below it,
    // so h - W has the sign of d near every shore for any seed. Each side has a
    // floor and a ceiling that meet at the shoreline (d = 0) and open up with
    // distance (70 m of freedom at 1 km, 550 m at 5 km); smooth min/max blends
    // leave the data untouched wherever it is well inside the bounds.
    const a = d < 0 ? -d : d;
    const ramp = 4 * (a / 0.6) / (1 + a / 0.6); // 0 at the shore, 4 m inland / below
    const room = 60 * a + 10 * a * a;
    const k = Math.min(20, 6 * a, 2 * ramp);
    if (d >= 0) {
      // Floor: the water level, fading beyond ~5 km (far from a shore the data
      // alone shapes the land). Ceiling: the full water level plus the freedom.
      const a3 = (a / 3) * (a / 3);
      const lo = W / (1 + a3 * a3) + ramp;
      const hi = W + ramp + room;
      h = smin(-smin(-h, -lo, k), hi, Math.min(40, 0.25 * (hi - lo)));
    } else {
      // The bed drops 40 m per km from the shore, about as steeply as land rises,
      // so the shoreline crosses mesh triangles mid-edge instead of snapping to
      // the vertex grid (a film of water over a flat bed reads as a sawtooth).
      const hi = W - ramp - 40 * a;
      h = -smin(-smin(h, hi, k), -(hi - room), Math.min(40, 0.25 * room));
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
    const b = ed.biome; // tree, shrub, herb, bare, ice, tundra
    const tree = sampleBilinear(b, lat, lon, 0);
    const shrub = sampleBilinear(b, lat, lon, 1);
    const herb = sampleBilinear(b, lat, lon, 2);
    const bare = sampleBilinear(b, lat, lon, 3);
    const ice = sampleBilinear(b, lat, lon, 4);
    const tun = sampleBilinear(b, lat, lon, 5);
    const sum = tree + shrub + herb + bare + ice + tun;
    // Shares of the mapped classes, faded continuously toward neutral where a
    // cell holds little or no land-cover data (coastal cells, the high Arctic).
    const cover = sstep(0.02, 0.15, sum);
    const inv = sum > 1e-6 ? 1 / sum : 0;
    // Aridity proxy: grass and crops in shrub/bare country read dry, not green.
    const arid = (shrub + bare) * inv;
    const green = tree + herb * (1 - arid);
    const veg = 0.3 + (green * inv - 0.3) * cover;
    const treeShare = tree * inv * cover;
    const iceShare = ice * inv * cover;
    const sandShare = (bare + 0.5 * shrub + 0.4 * herb * arid) * inv * cover;
    const dryShare = (bare + tun * 0.5) * inv * cover;
    // Snow above a latitude-dependent line (real metres), lowered by up to 1.4 km
    // in cells with mapped glaciers; the land-cover grid is too coarse to place
    // the ice, so it goes on the high ground, down to ~1 km below the line.
    // Heights here are the data's (regional relief uncompressed) plus the infill.
    const hd = h + (eData - e);
    const snowLine = 5200 - 5600 * (lat / 75) * (lat / 75) - 1400 * sstep(0.01, 0.12, iceShare);
    const snow = sstep(snowLine - 300, snowLine + 500, hd);
    const glacier = iceShare * sstep(snowLine - 1300, snowLine - 300, hd);
    const vn = n.v(px / 3000, py / 3000, pz / 3000);
    if (d < 0) {
      // Under water: sand and silt, independent of the land cover.
      out.biome = 0;
      out.variation = sat(0.45 + 0.25 * vn);
      out.special = 0;
      out.rockiness = 0.1;
    } else {
      out.biome = veg;
      // High variation: dark forest in the vegetated palette, bright sand in the dry one.
      out.variation = sat(0.3 + 0.55 * Math.max(treeShare, sandShare) + 0.2 * vn);
      out.special = Math.max(glacier, snow);
      out.rockiness = sat(mount * (0.35 + 0.6 * dryShare) + 0.25 * (1 - veg) * mount);
    }
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

  // ------------------------------------------------------- Sol surfaces
  // Procedural surfaces for the other Sol bodies: broad seeded undulations,
  // large real features at their coordinates (features.ts, Mars and Moon),
  // seeded craters and detail as infill. Relief in real metres, gameplay / 5.

  private readonly fs = { h: 0, mare: 0, scar: 0 };
  private readonly crat = { h: 0, floor: 0 };

  private featured(nx: number, ny: number, nz: number, out: SurfaceInfo): SurfaceInfo {
    const n = this.n;
    const R = this.R;
    const px = nx * R;
    const py = ny * R;
    const pz = nz * R;
    const zone = this.def.explore === 'zone';
    const reliefM = zone ? 0 : 1;
    const base = reliefM * (700 * fbm(n.b, px / 12000, py / 12000, pz / 12000, 3) + 160 * fbm(n.b2, px / 2600, py / 2600, pz / 2600, 2));
    const f = this.features
      ? this.features.sample(nx, ny, nz, this.fs, n.w1(px / 1200, py / 1200, pz / 1200), n.w2(px / 260, py / 260, pz / 260))
      : null;
    const realH = base + (f ? f.h : 0);
    this.craterField(px, py, pz, this.crat);
    const detail = fbm(n.d, px / 140, py / 140, pz / 140, 3);
    out.height = (this.def.reliefZero ?? 0) + realH / ELEVATION_DIVISOR + this.crat.h + detail * (zone ? 0.3 : 2.2);
    const sinLat = nx * this.def.frame.north[0] + ny * this.def.frame.north[1] + nz * this.def.frame.north[2];
    const v = 0.5 + 0.5 * n.v(px / 2600, py / 2600, pz / 2600);
    const mare = f ? f.mare : 0;
    const scar = f ? f.scar : 0;
    switch (this.def.id) {
      case 'moon':
        // Dark maria (biome B), bright highlands (A); fresh crater floors and walls read brighter.
        out.biome = mare;
        out.variation = v;
        out.special = sat(0.6 * scar + 0.4 * this.crat.floor) * (1 - 0.6 * mare);
        out.rockiness = sat(0.15 + 0.6 * scar);
        break;
      case 'mars': {
        // Dark basaltic albedo regions (B; Syrtis Major, Acidalium, ...) and slightly darker
        // lowland plains over bright dusty ground (A); polar ice caps.
        out.biome = sat(Math.max(mare, 0.3 * sstep(-1500, -3500, realH)) + 0.12 * (v - 0.5));
        out.variation = v;
        out.special = Math.max(sstep(0.955, 0.975, sinLat), sstep(-0.985, -0.995, sinLat));
        out.rockiness = sat(0.1 + 0.7 * scar + 0.3 * this.crat.floor);
        break;
      }
      default:
        out.biome = sstep(0.35, 0.65, v);
        out.variation = v;
        out.special = 0;
        out.rockiness = sat(0.15 + 0.5 * scar + 0.3 * this.crat.floor);
    }
    return out;
  }

  /** Seeded crater field (gameplay metres) from the body's crater scales; out.floor is the crater-floor weight. */
  private craterField(px: number, py: number, pz: number, out: { h: number; floor: number }): void {
    const R = this.R;
    let h = 0;
    let floorness = 0;
    for (let si = 0; si < this.craterScales.length; si++) {
      const sc = this.craterScales[si];
      if (sc.prob <= 0) continue;
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
              const fl = 1 - x;
              if (fl > floorness) floorness = fl;
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
    out.h = h;
    out.floor = floorness;
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
