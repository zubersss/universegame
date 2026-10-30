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
}

export type EarthRasters = Record<LayerName, Raster>;

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

const LAYER_URLS: Record<LayerName, string> = {
  elevation: new URL('../data/earth/earth-elevation.bin', import.meta.url).href,
  coast: new URL('../data/earth/earth-coast.bin', import.meta.url).href,
  water: new URL('../data/earth/earth-water.bin', import.meta.url).href,
  biome: new URL('../data/earth/earth-biome.bin', import.meta.url).href,
};

export type FetchBytes = (layer: LayerName, url: string) => Promise<ArrayBuffer | Uint8Array>;

async function defaultFetch(_layer: LayerName, url: string): Promise<ArrayBuffer> {
  const res = await fetch(url);
  if (!res.ok) throw new Error(`Earth data ${url}: HTTP ${res.status}`);
  return res.arrayBuffer();
}

let rasters: EarthRasters | null = null;
let pending: Promise<EarthRasters> | null = null;

/** Decoded rasters if loaded in this thread, else null. */
export function earthData(): EarthRasters | null {
  return rasters;
}

/** Load (once per thread) and decode all Earth layers; resolves to the shared rasters. */
export function loadEarthData(fetchBytes: FetchBytes = defaultFetch): Promise<EarthRasters> {
  if (rasters) return Promise.resolve(rasters);
  if (!pending) {
    const layers = Object.keys(LAYER_URLS) as LayerName[];
    pending = Promise.all(
      layers.map(async (name) => {
        const m = (meta.layers as Record<LayerName, LayerMeta>)[name];
        const d = await decodeLsr(await fetchBytes(name, LAYER_URLS[name]));
        if (d.width !== m.width || d.height !== m.height || d.channels !== m.channels) throw new Error(`Earth layer ${name}: shape mismatch`);
        const r: Raster = { width: d.width, height: d.height, channels: d.channels, res: m.res, scale: m.scale, offset: m.offset, data: d.data };
        return [name, r] as const;
      }),
    ).then(
      (entries) => {
        rasters = Object.fromEntries(entries) as EarthRasters;
        return rasters;
      },
      (err) => {
        pending = null; // allow a retry after a network failure
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
  let x = (lon + 180) / r.res;
  let y = (90 - lat) / r.res;
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
