import { DataTexture, LinearFilter, LinearMipmapLinearFilter, NoColorSpace, RepeatWrapping, RGBAFormat, UnsignedByteType } from 'three';

// Seamless (periodic) procedural detail texture for terrain. Data channels,
// not colors: R = fine albedo variation, G = crack/strata network,
// B = pebble/grain, A = bump height. Uses only lattice hashing (tileable).

function hash2(x: number, y: number, seed: number): number {
  let h = Math.imul(x | 0, 0x27d4eb2d) ^ Math.imul(y | 0, 0x165667b1) ^ seed;
  h = Math.imul(h ^ (h >>> 15), 0x85ebca6b);
  h = Math.imul(h ^ (h >>> 13), 0xc2b2ae35);
  h ^= h >>> 16;
  return (h >>> 0) / 4294967296;
}

const mod = (a: number, n: number) => ((a % n) + n) % n;

function valueNoise(u: number, v: number, period: number, seed: number): number {
  const x = u * period;
  const y = v * period;
  const xi = Math.floor(x);
  const yi = Math.floor(y);
  const fx = x - xi;
  const fy = y - yi;
  const sx = fx * fx * (3 - 2 * fx);
  const sy = fy * fy * (3 - 2 * fy);
  const a = hash2(mod(xi, period), mod(yi, period), seed);
  const b = hash2(mod(xi + 1, period), mod(yi, period), seed);
  const c = hash2(mod(xi, period), mod(yi + 1, period), seed);
  const d = hash2(mod(xi + 1, period), mod(yi + 1, period), seed);
  return a + (b - a) * sx + (c - a) * sy + (a - b - c + d) * sx * sy;
}

function fbm(u: number, v: number, base: number, oct: number, seed: number): number {
  let s = 0;
  let amp = 0.5;
  let p = base;
  let n = 0;
  for (let i = 0; i < oct; i++) {
    s += valueNoise(u, v, p, seed + i * 101) * amp;
    n += amp;
    amp *= 0.5;
    p *= 2;
  }
  return s / n;
}

/** Periodic Worley: returns [F1, F2] distances in cell units. */
function worley(u: number, v: number, period: number, seed: number): [number, number] {
  const x = u * period;
  const y = v * period;
  const xi = Math.floor(x);
  const yi = Math.floor(y);
  let f1 = 9;
  let f2 = 9;
  for (let j = -1; j <= 1; j++) {
    for (let i = -1; i <= 1; i++) {
      const cx = xi + i;
      const cy = yi + j;
      const px = cx + hash2(mod(cx, period), mod(cy, period), seed);
      const py = cy + hash2(mod(cx, period), mod(cy, period), seed + 7);
      const d = Math.sqrt((px - x) * (px - x) + (py - y) * (py - y));
      if (d < f1) {
        f2 = f1;
        f1 = d;
      } else if (d < f2) f2 = d;
    }
  }
  return [f1, f2];
}

export function makeTerrainDetailTexture(size = 256): DataTexture {
  const data = new Uint8Array(size * size * 4);
  for (let y = 0; y < size; y++) {
    for (let x = 0; x < size; x++) {
      const u = x / size;
      const v = y / size;
      const r = fbm(u, v, 8, 5, 11);
      const [c1, c2] = worley(u, v, 9, 23);
      const crack = Math.min(1, (c2 - c1) * 3.2); // 0 on cell edges
      const [p1] = worley(u, v, 26, 37);
      const pebble = Math.max(0, 1 - p1 * 1.6);
      const strata = 0.5 + 0.5 * Math.sin((v * 6 + fbm(u, v, 4, 3, 5) * 1.5) * Math.PI * 2);
      const g = crack * (0.75 + 0.25 * strata);
      const h = 0.45 * r + 0.3 * crack + 0.25 * pebble;
      const o = (y * size + x) * 4;
      data[o] = Math.round(r * 255);
      data[o + 1] = Math.round(g * 255);
      data[o + 2] = Math.round(pebble * 255);
      data[o + 3] = Math.round(Math.min(1, h) * 255);
    }
  }
  const t = new DataTexture(data, size, size, RGBAFormat, UnsignedByteType);
  t.wrapS = RepeatWrapping;
  t.wrapT = RepeatWrapping;
  t.magFilter = LinearFilter;
  t.minFilter = LinearMipmapLinearFilter;
  t.generateMipmaps = true;
  t.colorSpace = NoColorSpace;
  t.anisotropy = 4;
  t.needsUpdate = true;
  return t;
}
