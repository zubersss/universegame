// W3: the Earth dataset as shipped in src/data/earth/ — format, integrity,
// projection (longitude direction, pole rows, seam), units, nodata, and known
// places (Everest region high, Challenger Deep low, land fraction ≈ 29%).
import { createHash } from 'node:crypto';
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { beforeAll, describe, expect, it } from 'vitest';
import { EARTH_META, asind, atan2d, decodeLsr, installEarthData, loadEarthData, sampleBilinear, sampleCubic, sampleElevation, sincosd, type EarthRasters, type LayerName, type Raster } from '../src/world/earthData';

const dir = fileURLToPath(new URL('../src/data/earth/', import.meta.url));
const layers = EARTH_META.layers as Record<LayerName, { file: string; sha256Decoded: string; width: number; height: number; channels: number; res: number; bytes: number }>;
let E: EarthRasters;

const readLayer = (name: LayerName) => readFileSync(dir + layers[name].file);

beforeAll(async () => {
  E = await loadEarthData(async (_name, _url, file) => readFileSync(dir + file));
  installEarthData(E);
});

/** Area-weighted fraction of nodes satisfying `pred` (duplicate seam column excluded). */
function areaFraction(r: Raster, pred: (v: number) => boolean): number {
  let num = 0;
  let den = 0;
  const half = (r.res * Math.PI) / 360;
  for (let j = 0; j < r.height; j++) {
    const lat = ((90 - j * r.res) * Math.PI) / 180;
    const w = Math.sin(Math.min(lat + half, Math.PI / 2)) - Math.sin(Math.max(lat - half, -Math.PI / 2));
    for (let i = 0; i < r.width - 1; i++) {
      den += w;
      if (pred(r.data[j * r.width + i] * r.scale + r.offset)) num += w;
    }
  }
  return num / den;
}

/** Extremes of the raw raster over a lat/lon box (inclusive node range). */
function boxStats(r: Raster, lat0: number, lat1: number, lon0: number, lon1: number) {
  const j0 = Math.round((90 - lat1) / r.res);
  const j1 = Math.round((90 - lat0) / r.res);
  const i0 = Math.round((lon0 + 180) / r.res);
  const i1 = Math.round((lon1 + 180) / r.res);
  let min = Infinity;
  let max = -Infinity;
  const vals: number[] = [];
  for (let j = j0; j <= j1; j++) {
    for (let i = i0; i <= i1; i++) {
      const v = r.data[j * r.width + i] * r.scale + r.offset;
      vals.push(v);
      if (v < min) min = v;
      if (v > max) max = v;
    }
  }
  vals.sort((a, b) => a - b);
  return { min, max, median: vals[vals.length >> 1] };
}

describe('Earth dataset files (W3)', () => {
  it('decode to the documented shapes and match the recorded checksums', async () => {
    for (const name of Object.keys(layers) as LayerName[]) {
      const m = layers[name];
      const bytes = readLayer(name);
      expect(bytes.length, name).toBe(m.bytes);
      const d = await decodeLsr(bytes);
      expect([d.width, d.height, d.channels], name).toEqual([m.width, m.height, m.channels]);
      const raw = Buffer.from(d.data.buffer, d.data.byteOffset, d.data.byteLength);
      expect(createHash('sha256').update(raw).digest('hex'), name).toBe(m.sha256Decoded);
      // Node grid: W = 360/res + 1, H = 180/res + 1.
      expect(m.width).toBe(Math.round(360 / m.res) + 1);
      expect(m.height).toBe(Math.round(180 / m.res) + 1);
    }
  });

  it('stays within the 8 MB lazy data budget', () => {
    const total = Object.values(layers).reduce((n, l) => n + l.bytes, 0) + EARTH_META.regions.reduce((n, r) => n + r.bytes, 0);
    expect(total).toBe(EARTH_META.totalBytes);
    expect(total).toBeLessThan(8 * 1024 * 1024);
  });

  it('ships the Southern Alps regional grid intact, from public-domain sources only', async () => {
    expect(EARTH_META.regions.map((r) => r.name)).toEqual(['southern-alps']);
    const m = EARTH_META.regions[0];
    const bytes = readFileSync(dir + m.file);
    expect(bytes.length).toBe(m.bytes);
    const d = await decodeLsr(bytes);
    expect([d.width, d.height, d.channels]).toEqual([m.width, m.height, 1]);
    const raw = Buffer.from(d.data.buffer, d.data.byteOffset, d.data.byteLength);
    expect(createHash('sha256').update(raw).digest('hex')).toBe(m.sha256Decoded);
    expect(m.width).toBe(Math.round((m.east - m.west) / m.res) + 1);
    expect(m.height).toBe(Math.round((m.north - m.south) / m.res) + 1);
    // The route lies well inside (the grid fades in over its outer 0.25 deg).
    for (const [lat, lon] of [[-42.72, 170.95], [-43.39, 170.18], [-43.595, 170.142], [-43.05, 170.62]]) {
      expect(lat).toBeLessThan(m.north - 0.25);
      expect(lat).toBeGreaterThan(m.south + 0.25);
      expect(lon).toBeGreaterThan(m.west + 0.25);
      expect(lon).toBeLessThan(m.east - 0.25);
    }
    expect(m.source.imagerySources.every((x: string) => ['srtm', 'gmted', 'etopo1'].includes(x))).toBe(true);
    expect(m.source.tiles.length).toBe(25);
    expect(EARTH_META.credits.some((c: string) => /Southern Alps/.test(c) && /U\.S\. Geological Survey/.test(c))).toBe(true);
  });

  it('resolves the Southern Alps where the global grid only has a plateau', () => {
    const cs = { v: 0, dLon: 0, dLat: 0, region: 0 };
    const at = (lat: number, lon: number) => ({ ...sampleElevation(E, lat, lon, cs) });
    const aoraki = at(-43.595, 170.142);
    expect(aoraki.region).toBe(1);
    expect(aoraki.v).toBeGreaterThan(3200); // real summit 3,724 m; ~225 m source pixels
    expect(sampleBilinear(E.elevation, -43.595, 170.142)).toBeLessThan(2600); // the 10' grid
    expect(at(-42.717, 170.967).v).toBeLessThan(80); // Hokitika, on the coastal plain
    expect(at(-42.6, 170.5).v).toBeLessThan(-100); // Tasman Sea (ETOPO1 bathymetry)
    expect(at(-43.47, 170.18).v).toBeGreaterThan(at(-43.39, 170.18).v); // glacier rises toward the divide
    // Outside the region nothing changes.
    expect(at(-40, 175).v).toBe(sampleCubic(E.elevation, -40, 175, { v: 0, dLon: 0, dLat: 0 }).v);
    expect(at(-40, 175).region).toBe(0);
  });

  it('fades the regional grid in smoothly (value and gradient continuous across its edge band)', () => {
    const cs = { v: 0, dLon: 0, dLat: 0, region: 0 };
    // Walk east across the west edge band and north across the south edge band in 0.0005 deg steps.
    for (const [lat0, lon0, dLat, dLon] of [[-43.2, 169.1, 0, 1], [-44.3, 170.5, 1, 0]]) {
      let prev = sampleElevation(E, lat0, lon0, cs).v;
      let worst = 0;
      for (let k = 1; k <= 1000; k++) {
        const lat = lat0 + dLat * k * 0.0005;
        const lon = lon0 + dLon * k * 0.0005;
        const s0 = { ...sampleElevation(E, lat, lon, cs) };
        // The analytic gradient predicts the step (C1 blend), to within the curvature of the fields.
        const pred = prev + ((dLat ? s0.dLat : s0.dLon) * 0.0005);
        worst = Math.max(worst, Math.abs(s0.v - pred));
        prev = s0.v;
      }
      expect(worst, `${lat0},${lon0}`).toBeLessThan(15); // metres per 55 m step: no jump
    }
  });

  it('repeats column 0 as the last column (seam) and has constant pole rows', () => {
    for (const name of Object.keys(layers) as LayerName[]) {
      const r = E[name];
      const n = r.width * r.height;
      for (let c = 0; c < r.channels; c++) {
        for (let j = 0; j < r.height; j++) {
          expect(r.data[c * n + j * r.width], `${name} seam row ${j}`).toBe(r.data[c * n + j * r.width + r.width - 1]);
        }
        for (const j of [0, r.height - 1]) {
          const v0 = r.data[c * n + j * r.width];
          for (let i = 1; i < r.width; i++) {
            if (r.data[c * n + j * r.width + i] !== v0) throw new Error(`${name} pole row ${j} not constant at ${i}`);
          }
        }
      }
    }
  });

  it('samples the elevation raster in metres with the right orientation', () => {
    const z = E.elevation;
    expect(layers.elevation.res).toBeCloseTo(1 / 6, 12);
    // Units: metres (not km or feet).
    const everest = boxStats(z, 27.5, 28.5, 86.5, 87.5);
    expect(everest.max).toBeGreaterThan(5000);
    expect(everest.max).toBeLessThan(8900);
    expect(boxStats(z, 30, 34, 80, 95).median).toBeGreaterThan(4000); // Tibetan Plateau
    const challenger = boxStats(z, 10.5, 12, 141.5, 143);
    expect(challenger.min).toBeLessThan(-8000);
    expect(challenger.min).toBeGreaterThan(-11100);
    // Everest region is the highest area of the planet in the data.
    let max = -Infinity;
    let at = [0, 0];
    for (let j = 0; j < z.height; j++) for (let i = 0; i < z.width; i++) if (z.data[j * z.width + i] > max) { max = z.data[j * z.width + i]; at = [90 - j * z.res, -180 + i * z.res]; }
    expect(at[0]).toBeGreaterThan(26);
    expect(at[0]).toBeLessThan(37);
    expect(at[1]).toBeGreaterThan(70);
    expect(at[1]).toBeLessThan(100);
    // Longitude runs west to east: Australia at +135, open Pacific at -135; Congo at +25, Atlantic at -25.
    expect(sampleBilinear(z, -25, 135)).toBeGreaterThan(100);
    expect(sampleBilinear(z, -25, -135)).toBeLessThan(-2000);
    expect(sampleBilinear(z, 0, 25)).toBeGreaterThan(300);
    expect(sampleBilinear(z, 0, -25)).toBeLessThan(-2000);
    // Latitude runs north (row 0) to south: Siberia at +60, Southern Ocean at -60.
    expect(sampleBilinear(z, 60, 100)).toBeGreaterThan(0);
    expect(sampleBilinear(z, -60, 100)).toBeLessThan(-2000);
    // Pole rows: Arctic Ocean floor in the north, Antarctic ice plateau in the south.
    expect(sampleBilinear(z, 90, 0)).toBeLessThan(-2000);
    expect(sampleBilinear(z, -90, 0)).toBeGreaterThan(2000);
    expect(sampleBilinear(z, 72, -40)).toBeGreaterThan(2000); // Greenland ice sheet
  });

  it('has no nodata left', () => {
    expect(layers.elevation).toHaveProperty('nodata', null);
    const z = E.elevation.data;
    for (let k = 0; k < z.length; k++) if (z[k] <= -32767 || z[k] >= 32767) throw new Error(`nodata-like value at ${k}`);
  });

  it('puts about 29% of the surface on land', () => {
    const coastLand = areaFraction(E.coast, (v) => v > 0);
    expect(coastLand).toBeGreaterThan(0.27);
    expect(coastLand).toBeLessThan(0.31);
    const demLand = areaFraction(E.elevation, (v) => v > 0);
    expect(demLand).toBeGreaterThan(0.27);
    expect(demLand).toBeLessThan(0.31);
  });

  it('classifies known coasts, islands and lakes', () => {
    const land = (lat: number, lon: number) => sampleBilinear(E.coast, lat, lon) > 0;
    expect(land(0, -30)).toBe(false);
    expect(land(0, 25)).toBe(true);
    expect(land(-25, 135)).toBe(true);
    expect(land(-25, -135)).toBe(false);
    expect(land(42, 50.5)).toBe(false); // Caspian Sea
    expect(land(-1, 33)).toBe(false); // Lake Victoria
    expect(land(47.7, -87.5)).toBe(false); // Lake Superior
    expect(land(72, -40)).toBe(true); // Greenland
    expect(land(-81, 180)).toBe(true); // Ross Ice Shelf
    expect(land(19.6, -155.5)).toBe(true); // Hawaiʻi
    expect(land(7.9, 80.7)).toBe(true); // Sri Lanka
    expect(land(42.5, 12.5)).toBe(true); // Italy
    expect(land(39, 5)).toBe(false); // Balearic Sea
  });

  it('gives lakes a level and the ocean zero', () => {
    const w = (lat: number, lon: number) => sampleBilinear(E.water, lat, lon);
    expect(w(0, -30)).toBe(0);
    expect(w(-40, 60)).toBe(0);
    // Lake Victoria (real surface 1,134 m): the interim DEM's spurious lake pit pulls the estimate low.
    expect(w(-1, 33)).toBeGreaterThan(600);
    expect(w(-1, 33)).toBeLessThan(1400);
    // Highland and lowland lakes against commonly cited surface elevations (estimates, ±150 m).
    const lakes = Object.fromEntries((EARTH_META.layers.water.lakes as { name: string | null; level: number }[]).map((l) => [l.name, l.level]));
    for (const [name, real] of [['Lago Titicaca', 3812], ['Lake Sevan', 1900], ['Lake Tana', 1788], ['Qinghai Hu', 3196], ['Nam Co', 4718], ['Lake Superior', 183], ['Great Slave Lake', 156], ['Lake Balkhash', 341]] as const) {
      expect(Math.abs(lakes[name] - real), name).toBeLessThan(150);
    }
    expect(w(47.7, -87.5)).toBeGreaterThan(100); // Lake Superior (183 m)
    expect(w(47.7, -87.5)).toBeLessThan(450);
    // Natural Earth draws the Caspian as part of the sea (a hole in the land), so it takes the ocean level 0 (real −28 m).
    expect(w(42, 50.5)).toBe(0);
    expect(w(31.5, 35.5)).toBeGreaterThanOrEqual(1); // Dead Sea (−430 m real): lake levels are at least +1 m
  });

  it('maps land cover to plausible dominant classes', () => {
    const names = EARTH_META.layers.biome.channelNames as string[];
    expect(names).toEqual(['tree', 'shrub', 'herb', 'bare', 'ice', 'tundra']);
    const dominant = (lat: number, lon: number) => {
      let best = -1;
      let k = -1;
      for (let c = 0; c < names.length; c++) {
        const v = sampleBilinear(E.biome, lat, lon, c);
        if (v > best) { best = v; k = c; }
      }
      return names[k];
    };
    expect(dominant(-3, -60)).toBe('tree'); // Amazon
    expect(dominant(23, 10)).toBe('bare'); // Sahara
    expect(dominant(72, -40)).toBe('ice'); // Greenland
    expect(dominant(62, 100)).toBe('tree'); // Siberian taiga
    expect(dominant(40, -100)).toBe('herb'); // Great Plains
    expect(dominant(-25, 133)).toBe('shrub'); // Australian interior
  });
});

describe('raster sampling and deterministic angles', () => {
  it('is continuous across the ±180° seam and single-valued at the poles', () => {
    for (const name of ['elevation', 'coast', 'water'] as LayerName[]) {
      const r = E[name];
      for (const lat of [-70, -16.5, 0, 33.3, 65]) {
        expect(sampleBilinear(r, lat, 180)).toBe(sampleBilinear(r, lat, -180));
        expect(Math.abs(sampleBilinear(r, lat, 180 - 1e-9) - sampleBilinear(r, lat, -180 + 1e-9))).toBeLessThan(1e-3);
      }
      for (const lon of [-180, -97, 0, 45.5, 180]) {
        expect(sampleBilinear(r, 90, lon)).toBe(sampleBilinear(r, 90, 0));
        expect(sampleBilinear(r, -90, lon)).toBe(sampleBilinear(r, -90, 0));
      }
    }
  });

  it('matches Math.atan2 / Math.asin to double precision with arithmetic only', () => {
    let s = 12345;
    const rnd = () => ((s = (s * 1103515245 + 12345) % 2147483648) / 2147483648) * 2 - 1;
    let worst = 0;
    for (let k = 0; k < 20000; k++) {
      const y = rnd() * (k % 3 === 0 ? 1e-6 : 10);
      const x = rnd() * (k % 5 === 0 ? 1e-6 : 10);
      worst = Math.max(worst, Math.abs(atan2d(y, x) - Math.atan2(y, x)));
      const z = rnd();
      worst = Math.max(worst, Math.abs(asind(z) - Math.asin(z)));
    }
    expect(worst).toBeLessThan(1e-13);
    const sc = { s: 0, c: 0 };
    let worstSc = 0;
    for (let k = 0; k < 20000; k++) {
      const a = rnd() * 20;
      sincosd(a, sc);
      worstSc = Math.max(worstSc, Math.abs(sc.s - Math.sin(a)), Math.abs(sc.c - Math.cos(a)));
    }
    expect(worstSc).toBeLessThan(1e-14);
    expect(atan2d(0, -1)).toBeCloseTo(Math.PI, 15);
    expect(atan2d(1, 0)).toBeCloseTo(Math.PI / 2, 15);
    expect(asind(1)).toBeCloseTo(Math.PI / 2, 15);
  });
});
