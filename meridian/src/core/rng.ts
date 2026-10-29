// Deterministic hashing and seeded PRNG. Persistent world content (terrain,
// placement, discoveries, IDs) must only derive randomness from these,
// never from Math.random(), time, or job order.

/** FNV-1a 32-bit hash of a string. */
export function hashString(s: string): number {
  let h = 0x811c9dc5;
  for (let i = 0; i < s.length; i++) {
    h ^= s.charCodeAt(i);
    h = Math.imul(h, 0x01000193);
  }
  return h >>> 0;
}

/** Good-quality 32-bit integer finalizer (lowbias32). */
export function mix32(x: number): number {
  x = x >>> 0;
  x ^= x >>> 16;
  x = Math.imul(x, 0x7feb352d);
  x ^= x >>> 15;
  x = Math.imul(x, 0x846ca68b);
  x ^= x >>> 16;
  return x >>> 0;
}

/** Combine any number of 32-bit integers / strings into one 32-bit hash. */
export function hashCombine(...parts: (number | string)[]): number {
  let h = 0x9e3779b9;
  for (const p of parts) {
    const v = typeof p === 'string' ? hashString(p) : p >>> 0;
    h = mix32(h ^ (v + 0x9e3779b9 + ((h << 6) >>> 0) + (h >>> 2)));
  }
  return h >>> 0;
}

/** Hash to a float in [0, 1). */
export function hashFloat(...parts: (number | string)[]): number {
  return hashCombine(...parts) / 4294967296;
}

/** Hash three signed integer cell coordinates plus a salt to [0,1). */
export function hash3i(x: number, y: number, z: number, salt: number): number {
  let h = mix32((x | 0) ^ 0x27d4eb2d);
  h = mix32(h ^ (y | 0) ^ 0x165667b1);
  h = mix32(h ^ (z | 0) ^ 0x9e3779b1);
  h = mix32(h ^ salt);
  return h / 4294967296;
}

/** mulberry32: small, fast, explicitly seeded PRNG returning [0, 1). */
export function mulberry32(seed: number): () => number {
  let a = seed >>> 0;
  return () => {
    a = (a + 0x6d2b79f5) >>> 0;
    let t = a;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}
