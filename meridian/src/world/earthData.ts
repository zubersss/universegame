// Earth dataset (task W3): elevation, coastline distance and land-cover rasters
// built by scripts/data/build_earth.py into src/data/earth/. Lazy-loaded per
// body (fetched on first need, never in the main bundle), decoded once per
// thread, then sampled synchronously by the surface generator.
// Pure data and arithmetic: no Three.js, shared by the main thread and the workers.

import meta from '../data/earth/earth.json';

export type LayerName = 'elevation' | 'coast' | 'water' | 'biome';

export interface Raster {
  width: number;
  height: number;
  channels: number;
  /** Node spacing in degrees (row 0 = 90°N, column 0 = 180°W, last column duplicates column 0). */
  res: number;
  /** value = raw * scale + offset, in `units`. */
  scale: number;
  offset: number;
  data: Int16Array | Int8Array | Uint8Array;
  /** Regional grids: latitude of row 0 and longitude of column 0, no longitude wrap (global grids: 90, -180, wrap). */
  north?: number;
  west?: number;
  wrap?: boolean;
}

/** A regional elevation grid that overrides the global one inside its bounds (degrees). */
export interface RegionRaster extends Raster {
  name: string;
  north: number;
  south: number;
  west: number;
  east: number;
}

export type EarthRasters = Record<LayerName, Raster> & { regions: RegionRaster[] };

export const EARTH_META = meta;

const DTYPE: Record<number, 'int8' | 'uint8' | 'int16'> = { 1: 'int8', 2: 'uint8', 3: 'int16' };

async function gunzip(bytes: Uint8Array): Promise<Uint8Array> {
  if (bytes.length < 2 || bytes[0] !== 0x1f || bytes[1] !== 0x8b) return bytes; // already inflated (e.g. by the server)
  const stream = new Blob([bytes as BlobPart]).stream().pipeThrough(new DecompressionStream('gzip'));
  return new Uint8Array(await new Response(stream).arrayBuffer());
}

/**
 * Decode an LSR1 raster (format in scripts/data/build_earth.py): gzip, a
 * 16-byte header, then per channel the gradient-predicted, zigzag-coded
 * residuals (16-bit as a low-byte plane followed by a high-byte plane).
 */
export async function decodeLsr(input: ArrayBuffer | Uint8Array): Promise<{ width: number; height: number; channels: number; dtype: 'int8' | 'uint8' | 'int16'; data: Int16Array | Int8Array | Uint8Array }> {
  const b = await gunzip(input instanceof Uint8Array ? input : new Uint8Array(input));
  if (b.length < 16 || b[0] !== 0x4c || b[1] !== 0x53 || b[2] !== 0x52 || b[3] !== 0x31) throw new Error('Not an LSR1 raster');
  const dv = new DataView(b.buffer, b.byteOffset, b.byteLength);
  const width = dv.getUint32(4, true);
  const height = dv.getUint32(8, true);
  const dtype = DTYPE[b[12]];
  const channels = b[13];
  if (!dtype || b[14] !== 1) throw new Error('Unsupported LSR1 raster encoding');
  const n = width * height;
  const wide = dtype === 'int16';
  const expect = 16 + n * channels * (wide ? 2 : 1);
  if (b.length !== expect) throw new Error(`LSR1 size mismatch: ${b.length} != ${expect}`);
  const data = wide ? new Int16Array(n * channels) : dtype === 'int8' ? new Int8Array(n * channels) : new Uint8Array(n * channels);
  let src = 16;
  for (let c = 0; c < channels; c++) {
    const o = c * n;
    for (let k = 0; k < n; k++) {
      const z = wide ? b[src + k] | (b[src + n + k] << 8) : b[src + k];
      const r = (z >>> 1) ^ -(z & 1);
      const i = k % width;
      const left = i > 0 ? data[o + k - 1] : 0;
      let p: number;
      if (k < width) p = left;
      else if (i === 0) p = data[o + k - width];
      else p = left + data[o + k - width] - data[o + k - width - 1];
      data[o + k] = p + r; // typed-array store wraps modulo 2^bits, exactly undoing the encoder
    }
    src += n * (wide ? 2 : 1);
  }
  return { width, height, channels, dtype, data };
}

type LayerMeta = { file: string; width: number; height: number; channels: number; res: number; scale: number; offset: number };
type RegionMeta = LayerMeta & { name: string; north: number; south: number; west: number; east: number };

const LAYER_URLS: Record<LayerName, string> = {
  elevation: new URL('../data/earth/earth-elevation.bin', import.meta.url).href,
  coast: new URL('../data/earth/earth-coast.bin', import.meta.url).href,
  water: new URL('../data/earth/earth-water.bin', import.meta.url).href,
  biome: new URL('../data/earth/earth-biome.bin', import.meta.url).href,
};

/** Regional elevation grids (earth.json "regions"), each a static URL so the bundler emits the file. */
const REGION_URLS: Record<string, string> = {
  'southern-alps': new URL('../data/earth/earth-region-southern-alps.bin', import.meta.url).href,
};

/** Fetches one packaged file: `name` is a layer or `region:<name>`, `file` its name in src/data/earth/. */
export type FetchBytes = (name: string, url: string, file: string) => Promise<ArrayBuffer | Uint8Array>;

async function defaultFetch(_name: string, url: string): Promise<ArrayBuffer> {
  const res = await fetch(url);
  if (!res.ok) throw new Error(`Earth data ${url}: HTTP ${res.status}`);
  return res.arrayBuffer();
}

let rasters: EarthRasters | null = null;
let pending: Promise<EarthRasters> | null = null;
/** Consecutive failed loads and the earliest time (ms) of the next attempt: failures back off 2 s, 4 s, ... 60 s. */
let failures = 0;
let retryAt = 0;

/** Decoded rasters if loaded in this thread, else null. */
export function earthData(): EarthRasters | null {
  return rasters;
}

/**
 * Load (once per thread) and decode all Earth layers; resolves to the shared
 * rasters. After a failure, calls inside the back-off window reject at once
 * without fetching, so a lost connection never turns into a download loop.
 */
export function loadEarthData(fetchBytes: FetchBytes = defaultFetch): Promise<EarthRasters> {
  if (rasters) return Promise.resolve(rasters);
  if (!pending) {
    const wait = retryAt - Date.now();
    if (wait > 0) return Promise.reject(new Error(`Earth data unavailable (next attempt in ${Math.ceil(wait / 1000)} s)`));
    const layers = Object.keys(LAYER_URLS) as LayerName[];
    const regionMeta = (meta as unknown as { regions?: RegionMeta[] }).regions ?? [];
    const load = async (name: string, url: string, m: LayerMeta): Promise<Raster> => {
      const d = await decodeLsr(await fetchBytes(name, url, m.file));
      if (d.width !== m.width || d.height !== m.height || d.channels !== m.channels) throw new Error(`Earth ${name}: shape mismatch`);
      return { width: d.width, height: d.height, channels: d.channels, res: m.res, scale: m.scale, offset: m.offset, data: d.data };
    };
    pending = Promise.all([
      Promise.all(layers.map(async (name) => [name, await load(name, LAYER_URLS[name], (meta.layers as Record<LayerName, LayerMeta>)[name])] as const)),
      Promise.all(
        regionMeta.map(async (m): Promise<RegionRaster> => {
          const url = REGION_URLS[m.name];
          if (!url) throw new Error(`Earth region ${m.name}: no packaged file`);
          const r = await load(`region:${m.name}`, url, m);
          return { ...r, name: m.name, north: m.north, south: m.south, west: m.west, east: m.east, wrap: false };
        }),
      ),
    ]).then(
      ([entries, regions]) => {
        rasters = { ...(Object.fromEntries(entries) as Record<LayerName, Raster>), regions };
        failures = 0;
        return rasters;
      },
      (err) => {
        pending = null; // allow a retry after the back-off
        failures++;
        retryAt = Date.now() + Math.min(60_000, 2000 * 2 ** (failures - 1));
        throw err;
      },
    );
  }
  return pending;
}

/** Install already-decoded rasters (tests, or a thread that received them by message). */
export function installEarthData(r: EarthRasters): void {
  rasters = r;
}

/**
 * Bilinear sample of channel `ch` at latitude/longitude in degrees, in the
 * layer's units. Longitude must be in [-180, 180] (the duplicated seam column
 * makes ±180 identical); latitude is clamped to [-90, 90].
 */
export function sampleBilinear(r: Raster, lat: number, lon: number, ch = 0): number {
  const W = r.width;
  const H = r.height;
  let x = (lon - (r.west ?? -180)) / r.res;
  let y = ((r.north ?? 90) - lat) / r.res;
  x = x < 0 ? 0 : x > W - 1 ? W - 1 : x;
  y = y < 0 ? 0 : y > H - 1 ? H - 1 : y;
  let i = Math.floor(x);
  let j = Math.floor(y);
  if (i > W - 2) i = W - 2;
  if (j > H - 2) j = H - 2;
  const tx = x - i;
  const ty = y - j;
  const d = r.data;
  const o = ch * W * H + j * W + i;
  const a = d[o];
  const b = d[o + 1];
  const c = d[o + W];
  const e = d[o + W + 1];
  const top = a + (b - a) * tx;
  const bot = c + (e - c) * tx;
  return (top + (bot - top) * ty) * r.scale + r.offset;
}

/** Result of sampleCubic: value and its gradient in layer units per degree (east, north). */
export interface CubicSample {
  v: number;
  dLon: number;
  dLat: number;
}

/**
 * Uniform cubic B-spline sample of channel `ch` (C2 continuous, so terrain
 * shading shows no crease lines along raster cells), with its analytic
 * gradient. Longitude wraps with period width - 1 (the duplicated seam
 * column), rows clamp at the poles (constant pole rows keep it single-valued).
 * The spline smooths slightly: a node's value becomes (a + 4b + c) / 6 of its
 * neighbourhood in each direction.
 */
export function sampleCubic(r: Raster, lat: number, lon: number, out: CubicSample, ch = 0): CubicSample {
  const W = r.width;
  const H = r.height;
  const P = W - 1;
  const wrap = r.wrap !== false;
  let x = (lon - (r.west ?? -180)) / r.res;
  let y = ((r.north ?? 90) - lat) / r.res;
  x = x < 0 ? 0 : x > P ? P : x;
  y = y < 0 ? 0 : y > H - 1 ? H - 1 : y;
  let i = Math.floor(x);
  let j = Math.floor(y);
  if (i > P - 1) i = P - 1;
  if (j > H - 2) j = H - 2;
  const tx = x - i;
  const ty = y - j;
  const ux = 1 - tx;
  const uy = 1 - ty;
  const wx0 = (ux * ux * ux) / 6, wx1 = (3 * tx * tx * tx - 6 * tx * tx + 4) / 6, wx2 = (-3 * tx * tx * tx + 3 * tx * tx + 3 * tx + 1) / 6, wx3 = (tx * tx * tx) / 6;
  const dx0 = -(ux * ux) / 2, dx1 = (3 * tx * tx - 4 * tx) / 2, dx2 = (-3 * tx * tx + 2 * tx + 1) / 2, dx3 = (tx * tx) / 2;
  const wy0 = (uy * uy * uy) / 6, wy1 = (3 * ty * ty * ty - 6 * ty * ty + 4) / 6, wy2 = (-3 * ty * ty * ty + 3 * ty * ty + 3 * ty + 1) / 6, wy3 = (ty * ty * ty) / 6;
  const dy0 = -(uy * uy) / 2, dy1 = (3 * ty * ty - 4 * ty) / 2, dy2 = (-3 * ty * ty + 2 * ty + 1) / 2, dy3 = (ty * ty) / 2;
  // Global grids wrap in longitude (period W - 1); regional grids clamp at their edges.
  const c0 = wrap ? (i - 1 + P) % P : Math.max(i - 1, 0);
  const c1 = wrap ? i % P : i;
  const c2 = wrap ? (i + 1) % P : i + 1;
  const c3 = wrap ? (i + 2) % P : Math.min(i + 2, P);
  const d = r.data;
  const base = ch * W * H;
  let v = 0;
  let gx = 0;
  let gy = 0;
  for (let k = 0; k < 4; k++) {
    let row = j - 1 + k;
    row = row < 0 ? 0 : row > H - 1 ? H - 1 : row;
    const o = base + row * W;
    const a0 = d[o + c0], a1 = d[o + c1], a2 = d[o + c2], a3 = d[o + c3];
    const rv = a0 * wx0 + a1 * wx1 + a2 * wx2 + a3 * wx3;
    const rd = a0 * dx0 + a1 * dx1 + a2 * dx2 + a3 * dx3;
    const wy = k === 0 ? wy0 : k === 1 ? wy1 : k === 2 ? wy2 : wy3;
    const dy = k === 0 ? dy0 : k === 1 ? dy1 : k === 2 ? dy2 : dy3;
    v += rv * wy;
    gx += rd * wy;
    gy += rv * dy;
  }
  out.v = v * r.scale + r.offset;
  out.dLon = (gx * r.scale) / r.res;
  out.dLat = (-gy * r.scale) / r.res; // rows run north to south
  return out;
}

/** Elevation sample: value (m) and gradient (m per degree), plus the weight of the regional grid used. */
export interface ElevationSample extends CubicSample {
  /** 0 = global grid only, 1 = regional grid only. */
  region: number;
  /** The data elevation (m) whatever the gain: regional relief at full strength. */
  data?: number;
}

/** Regional grids fade in over this band inside their edges (degrees; starts a few nodes in, so the stencil stays inside). */
const REGION_FADE0 = 0.03;
const REGION_FADE1 = 0.25;
const _rs: CubicSample = { v: 0, dLon: 0, dLat: 0 };

/**
 * Elevation (m above mean sea level) with its gradient: the global grid,
 * overridden by a regional grid inside its bounds with a smooth fade (C1,
 * gradient included) over its outer band. `gain` scales the regional relief
 * relative to the global grid (1 = the data). Longitudes in [-180, 180];
 * regions do not straddle the antimeridian.
 */
export function sampleElevation(E: EarthRasters, lat: number, lon: number, out: ElevationSample, gain = 1): ElevationSample {
  sampleCubic(E.elevation, lat, lon, out);
  out.region = 0;
  out.data = out.v;
  for (const g of E.regions) {
    const dS = lat - g.south, dN = g.north - lat, dW = lon - g.west, dE = g.east - lon;
    let m = dS;
    let gLat = 1;
    let gLon = 0;
    if (dN < m) { m = dN; gLat = -1; gLon = 0; }
    if (dW < m) { m = dW; gLat = 0; gLon = 1; }
    if (dE < m) { m = dE; gLat = 0; gLon = -1; }
    if (m <= REGION_FADE0) continue;
    sampleCubic(g, lat, lon, _rs);
    const t = m >= REGION_FADE1 ? 1 : (m - REGION_FADE0) / (REGION_FADE1 - REGION_FADE0);
    const w = t * t * (3 - 2 * t) * gain;
    const dw = m >= REGION_FADE1 ? 0 : ((6 * t * (1 - t)) / (REGION_FADE1 - REGION_FADE0)) * gain;
    const dv = _rs.v - out.v;
    out.region = t * t * (3 - 2 * t);
    out.data = out.v + out.region * dv;
    out.dLon += w * (_rs.dLon - out.dLon) + dv * dw * gLon;
    out.dLat += w * (_rs.dLat - out.dLat) + dv * dw * gLat;
    out.v += w * dv;
    break; // regions do not overlap
  }
  return out;
}

// ---------------------------------------------------------------------------
// Deterministic angles. Only + − × ÷ and Math.sqrt (IEEE correctly rounded), so
// every thread and browser maps a direction to the same raster position.

const HALF_PI = 1.5707963267948966;
const PI = 3.141592653589793;

/** atan for |x| <= 1: six argument halvings (atan x = 2 atan(x / (1 + sqrt(1 + x²)))) then a short series. */
function atanUnit(x: number): number {
  for (let k = 0; k < 6; k++) x = x / (1 + Math.sqrt(1 + x * x));
  const z = x * x;
  // |x| <= tan(pi/256) after six halvings: the series to x^11 is exact to double precision.
  const s = x * (1 - z * (1 / 3 - z * (1 / 5 - z * (1 / 7 - z * (1 / 9 - z / 11)))));
  return s * 64;
}

/** Deterministic atan2(y, x) in radians, (−π, π]. */
export function atan2d(y: number, x: number): number {
  if (x === 0 && y === 0) return 0;
  const ax = x < 0 ? -x : x;
  const ay = y < 0 ? -y : y;
  let a = ay <= ax ? atanUnit(ay / ax) : HALF_PI - atanUnit(ax / ay);
  if (x < 0) a = PI - a;
  return y < 0 ? -a : a;
}

/** Deterministic asin(z) in radians for z in [−1, 1]. */
export function asind(z: number): number {
  const c = 1 - z * z;
  return atan2d(z, c > 0 ? Math.sqrt(c) : 0);
}

const RAD = 180 / PI;

/** Deterministic sin and cos (arithmetic only): quadrant reduction, then Taylor series on |x| <= pi/4. */
export function sincosd(angle: number, out: { s: number; c: number }): { s: number; c: number } {
  const q = Math.floor(angle / HALF_PI + 0.5);
  const x = angle - q * HALF_PI; // |x| <= pi/4 (plus rounding)
  const x2 = x * x;
  // Terms to x^17 / x^16: error below 1e-17 on |x| <= pi/4.
  const s = x * (1 - (x2 / 6) * (1 - (x2 / 20) * (1 - (x2 / 42) * (1 - (x2 / 72) * (1 - (x2 / 110) * (1 - (x2 / 156) * (1 - (x2 / 210) * (1 - x2 / 272))))))));
  const c = 1 - (x2 / 2) * (1 - (x2 / 12) * (1 - (x2 / 30) * (1 - (x2 / 56) * (1 - (x2 / 90) * (1 - (x2 / 132) * (1 - (x2 / 182) * (1 - x2 / 240)))))));
  const m = ((q % 4) + 4) % 4;
  out.s = m === 0 ? s : m === 1 ? c : m === 2 ? -s : -c;
  out.c = m === 0 ? c : m === 1 ? -s : m === 2 ? -c : s;
  return out;
}

/** Latitude/longitude in degrees of unit direction n in a body frame given by unit north and prime-meridian axes. */
export function latLonOf(
  nx: number, ny: number, nz: number,
  north: readonly number[], meridian: readonly number[], east: readonly number[],
  out: { lat: number; lon: number },
): { lat: number; lon: number } {
  const s = nx * north[0] + ny * north[1] + nz * north[2];
  const x = nx * meridian[0] + ny * meridian[1] + nz * meridian[2];
  const y = nx * east[0] + ny * east[1] + nz * east[2];
  // Latitude from the equatorial component directly (no 1 - s² cancellation near the poles).
  out.lat = atan2d(s, Math.sqrt(x * x + y * y)) * RAD;
  out.lon = atan2d(y, x) * RAD;
  return out;
}
