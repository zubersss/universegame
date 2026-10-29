// Celestial body definitions. Pure data: this module is shared by the main
// thread and the terrain worker, so it must not import Three.js.
// All distances are meters in system coordinates (right-handed).

import { hashCombine } from '../core/rng';

export type BodyId = 'ilex' | 'vesper' | 'cairn';
export const BODY_IDS: readonly BodyId[] = ['ilex', 'vesper', 'cairn'];

export const WORLD_SEED = 0x6d657231;
/** Bump when the surface generator changes in a way that alters geography. */
export const GENERATOR_VERSION = 1;
export const SAVE_SCHEMA_VERSION = 1;

/** Direction toward the (infinitely distant) sun, normalized. Fixed for the release. */
export const SUN_DIR: readonly [number, number, number] = (() => {
  const v = [-0.79, -0.215, -0.575];
  const l = Math.sqrt(v[0] * v[0] + v[1] * v[1] + v[2] * v[2]);
  return [v[0] / l, v[1] / l, v[2] / l] as const;
})();

export interface AtmosphereDef {
  /** Rayleigh scattering coefficients per meter at sea level (r,g,b). */
  rayleigh: [number, number, number];
  rayleighH: number;
  /** Mie (aerosol/dust) scattering coefficients per meter (r,g,b). */
  mie: [number, number, number];
  mieH: number;
  mieG: number;
  /** Sun radiance scale used by the sky shader. */
  sunIntensity: number;
  /** Faint night-side airglow (linear rgb). */
  airglow: [number, number, number];
}

export interface CloudLayerDef {
  altitude: number;
  thickness: number;
  coverage: number;
  scale: number; // feature wavelength in meters
  speed: number; // angular drift rad/s
  tint: [number, number, number];
  opacity: number;
  streak: number; // 0 = puffy, 1 = streaky
}

export interface BodyPalette {
  // sRGB hex colors; converted to linear where used.
  a1: number; a2: number; a3: number; // biome A ground / slope / accent
  b1: number; b2: number; b3: number; // biome B ground / slope / accent
  special: number; // deposits / ice / mineral accents
  proxyNight: number;
}

export interface BodyDef {
  id: BodyId;
  index: number;
  name: string;
  kind: 'planet' | 'moon';
  center: [number, number, number];
  radius: number;
  atmosphereHeight: number;
  gravity: number;
  maxHeight: number;
  /** Contact/max-detail quadtree level: ceil(log2(2R/128)). */
  maxLevel: number;
  seed: number;
  atmosphere: AtmosphereDef | null;
  clouds: CloudLayerDef[];
  palette: BodyPalette;
  biomeNames: [string, string];
  description: string;
}

function maxLevelFor(radius: number): number {
  return Math.ceil(Math.log2((2 * radius) / 128));
}

function seedFor(id: BodyId): number {
  return hashCombine(WORLD_SEED, GENERATOR_VERSION, id);
}

export const BODIES: Record<BodyId, BodyDef> = {
  ilex: {
    id: 'ilex',
    index: 0,
    name: 'Ilex',
    kind: 'planet',
    center: [0, 0, 0],
    radius: 60000,
    atmosphereHeight: 8000,
    gravity: 6,
    maxHeight: 900,
    maxLevel: maxLevelFor(60000),
    seed: seedFor('ilex'),
    atmosphere: {
      rayleigh: [4.2e-5, 1.12e-4, 1.6e-4],
      rayleighH: 1700,
      mie: [3.0e-5, 3.0e-5, 2.8e-5],
      mieH: 650,
      mieG: 0.78,
      sunIntensity: 22,
      airglow: [0.0025, 0.006, 0.006],
    },
    clouds: [
      { altitude: 2300, thickness: 500, coverage: 0.42, scale: 5200, speed: 0.000012, tint: [1.0, 0.98, 0.95], opacity: 0.85, streak: 0.15 },
      { altitude: 5400, thickness: 300, coverage: 0.3, scale: 9000, speed: 0.00002, tint: [0.97, 0.98, 1.0], opacity: 0.5, streak: 0.85 },
    ],
    palette: {
      // Albedos lean khaki: Ilex's low, reddened sun renders them as ochre.
      a1: 0xae9866, a2: 0xeee9dc, a3: 0x8f7c52, // chalk highlands: ochre ground, chalk faces, dry umber
      b1: 0xb4a272, b2: 0xd8ccae, b3: 0x2a5650, // teal grove lowlands: ochre soil, pale stone, teal
      special: 0x3f7a6a, // dark teal loam under the groves
      proxyNight: 0x0c1418,
    },
    biomeNames: ['Chalk Highlands', 'Teal Grove Lowlands'],
    description: 'A temperate world of chalk ridges and ochre plains, threaded with dark teal groves.',
  },
  vesper: {
    id: 'vesper',
    index: 1,
    name: 'Vesper',
    kind: 'planet',
    center: [800000, 0, -600000],
    radius: 45000,
    atmosphereHeight: 6000,
    gravity: 8,
    maxHeight: 1100,
    maxLevel: maxLevelFor(45000),
    seed: seedFor('vesper'),
    atmosphere: {
      rayleigh: [1.6e-5, 3.0e-5, 6.0e-5],
      rayleighH: 1300,
      mie: [1.1e-4, 7.6e-5, 4.8e-5],
      mieH: 900,
      mieG: 0.7,
      sunIntensity: 22,
      airglow: [0.006, 0.0035, 0.002],
    },
    clouds: [
      { altitude: 3800, thickness: 400, coverage: 0.26, scale: 7000, speed: 0.00001, tint: [1.0, 0.86, 0.72], opacity: 0.45, streak: 0.7 },
    ],
    palette: {
      a1: 0x9a4a2c, a2: 0x6e3020, a3: 0xc07a4e, // rust mesas: rust, deep oxide cliffs, banded tan
      b1: 0xd9c4a0, b2: 0xc2a57d, b3: 0xead9b8, // pale dunes
      special: 0x141416,
      proxyNight: 0x140c0a,
    },
    biomeNames: ['Rust Mesa Country', 'Pale Dune Sea'],
    description: 'A dry, dust-hazed world of terraced rust mesas and pale dune seas.',
  },
  cairn: {
    id: 'cairn',
    index: 2,
    name: 'Cairn',
    kind: 'moon',
    center: [450000, 120000, 300000],
    radius: 18000,
    atmosphereHeight: 0,
    gravity: 2.6,
    maxHeight: 600,
    maxLevel: maxLevelFor(18000),
    seed: seedFor('cairn'),
    atmosphere: null,
    clouds: [],
    palette: {
      a1: 0x8d9096, a2: 0x5f6268, a3: 0xb9bcc2, // silver highlands
      b1: 0x7b8088, b2: 0x9aa2ad, b3: 0xc8dcef, // rime basins
      special: 0xbfe0ff,
      proxyNight: 0x070809,
    },
    biomeNames: ['Silver Crater Highlands', 'Rime Basins'],
    description: 'An airless moon of overlapping craters, silver rock, and blue-shadowed ice.',
  },
};

export function bodyById(id: BodyId): BodyDef {
  return BODIES[id];
}

export function isBodyId(x: unknown): x is BodyId {
  return x === 'ilex' || x === 'vesper' || x === 'cairn';
}
