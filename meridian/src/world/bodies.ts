// Celestial body definitions. Pure data: this module is shared by the main
// thread and the terrain worker, so it must not import Three.js.
// All distances are meters in system coordinates (right-handed).

import { hashCombine } from '../core/rng';

export type BodyId = 'ilex' | 'vesper' | 'cairn' | 'orrin' | 'saro';
/** Every body, in navigation order (keys 1…N). Append new bodies; never reorder. */
export const BODY_IDS: readonly BodyId[] = ['ilex', 'vesper', 'cairn', 'orrin', 'saro'];

export const WORLD_SEED = 0x6d657231;
/** Bump when the surface generator changes in a way that alters geography. */
export const GENERATOR_VERSION = 1;
export const SAVE_SCHEMA_VERSION = 2;

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

/**
 * Optional per-body terrain material parameters (read by the terrain material;
 * pure data here so world definitions never import render code). Absent
 * fields fall back to the material's defaults.
 */
export interface TerrainLook {
  specialRough: number;
  specialSheen: number;
  bump: number;
  /** Horizontal rock banding 0..1 and its spacing (m). */
  strata: number;
  strataSpacing: number;
  /** Large-scale colour variation 0..1. */
  macro: number;
  /** Sediment colour in hollows (sRGB hex) and its amount 0..1. */
  sediment: number;
  sedimentAmount: number;
  /** Bare rock on high ground 0..1. */
  peakRock: number;
  /** Slope range [start, end] (as 1 - cos of the slope angle) over which rock replaces ground. */
  rockSlope: [number, number];
}

/** Per-body ambience profile for the audio (pure data). */
export interface AmbienceDef {
  /** Wind loudness scale, 0 = still air. */
  wind: number;
  /** Wind band centre in still air (Hz). */
  windTone: number;
  /** Height above the datum (m) where surface wind fades to half. */
  windAltitude: number;
  /** Tonal centre of ambient tones and music (Hz). */
  tonic: number;
  /** Scale degrees in semitones. */
  scale: number[];
  timbre: 'sine' | 'triangle';
  /** Mean seconds between ambient tones. */
  toneGap: number;
  /** Default footstep surface. */
  ground: 'soil' | 'sand' | 'rock' | 'ice' | 'salt' | 'moss';
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
  /**
   * Which survey the body's relay belongs to: the core survey (the game's
   * ending, transmitted with T) or the Extended Survey sent after it.
   */
  survey: 'core' | 'extended';
  look?: Partial<TerrainLook>;
  ambience?: AmbienceDef;
}

const PENTA = [0, 2, 4, 7, 9, 12, 14];

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
    survey: 'core',
    ambience: { wind: 1, windTone: 300, windAltitude: 1500, tonic: 220, scale: PENTA, timbre: 'triangle', toneGap: 16, ground: 'soil' },
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
    survey: 'core',
    ambience: { wind: 1, windTone: 300, windAltitude: 1200, tonic: 196, scale: PENTA, timbre: 'triangle', toneGap: 16, ground: 'sand' },
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
    survey: 'core',
    ambience: { wind: 0, windTone: 300, windAltitude: 0, tonic: 261.6, scale: PENTA, timbre: 'sine', toneGap: 16, ground: 'rock' },
  },
  orrin: {
    id: 'orrin',
    index: 3,
    name: 'Orrin',
    kind: 'planet',
    // Moved from the first proposal (-700, 80, 650 km) so the straight
    // Vesper–Orrin line clears Ilex's safety envelope (by ~47 km).
    center: [-720000, 240000, 600000],
    radius: 52000,
    atmosphereHeight: 9000,
    gravity: 9,
    maxHeight: 650,
    maxLevel: maxLevelFor(52000),
    seed: seedFor('orrin'),
    atmosphere: {
      // Dense and humid: strong, low-lying haze over a lilac-grey sky.
      rayleigh: [5.0e-5, 7.4e-5, 1.25e-4],
      rayleighH: 1900,
      mie: [6.5e-5, 6.5e-5, 7.0e-5],
      mieH: 520,
      mieG: 0.74,
      sunIntensity: 20,
      airglow: [0.004, 0.0035, 0.007],
    },
    clouds: [
      { altitude: 1900, thickness: 600, coverage: 0.55, scale: 6500, speed: 0.000009, tint: [0.92, 0.9, 0.96], opacity: 0.8, streak: 0.9 },
      { altitude: 6200, thickness: 350, coverage: 0.35, scale: 11000, speed: 0.000016, tint: [0.96, 0.95, 1.0], opacity: 0.45, streak: 0.95 },
    ],
    palette: {
      a1: 0x3e3c46, a2: 0x2a2930, a3: 0x5c5468, // basalt column highlands: dark basalt, column faces, weathered lilac
      b1: 0x5e4a78, b2: 0x4a4256, b3: 0x8a6ea4, // violet moss lowlands: moss, damp stone, bright moss
      special: 0x2f3c40, // wet valley floors
      proxyNight: 0x0c0a14,
    },
    biomeNames: ['Basalt Column Highlands', 'Violet Moss Lowlands'],
    description: 'A humid world of violet moss plains below stepped basalt highlands, its valleys full of slow fog.',
    survey: 'extended',
    ambience: { wind: 1.3, windTone: 220, windAltitude: 2500, tonic: 174.6, scale: [0, 3, 5, 7, 10, 12, 15], timbre: 'triangle', toneGap: 20, ground: 'moss' },
  },
  saro: {
    id: 'saro',
    index: 4,
    name: 'Saro',
    kind: 'planet',
    center: [300000, -150000, -950000],
    radius: 38000,
    atmosphereHeight: 4000,
    gravity: 5,
    maxHeight: 200,
    maxLevel: maxLevelFor(38000),
    seed: seedFor('saro'),
    atmosphere: {
      // Thin and bright: pale sky, little haze.
      rayleigh: [2.6e-5, 5.2e-5, 9.0e-5],
      rayleighH: 850,
      mie: [1.2e-5, 1.2e-5, 1.2e-5],
      mieH: 400,
      mieG: 0.8,
      sunIntensity: 26,
      airglow: [0.004, 0.002, 0.003],
    },
    clouds: [
      { altitude: 3000, thickness: 200, coverage: 0.12, scale: 9000, speed: 0.000014, tint: [1.0, 0.97, 0.97], opacity: 0.35, streak: 1.0 },
    ],
    palette: {
      a1: 0xe6c3c0, a2: 0xcf9fa0, a3: 0xf3e1da, // rose salt flats: pink crust, ridge faces, bright crust
      b1: 0x9ec9c0, b2: 0xc89a9c, b3: 0x5cc4bc, // brine pans: damp salt, rims, turquoise
      special: 0x3fb4ac, // open brine
      proxyNight: 0x140c10,
    },
    biomeNames: ['Rose Salt Flats', 'Brine Pan Shallows'],
    description: 'A bright, thin-aired salt desert: pink crust split into polygons around shallow turquoise brine pans.',
    survey: 'extended',
    ambience: { wind: 0.7, windTone: 520, windAltitude: 800, tonic: 293.7, scale: [0, 2, 5, 7, 9, 12, 14], timbre: 'sine', toneGap: 22, ground: 'salt' },
  },
};

/** Bodies of the core survey (its transmission ends the main expedition). */
export const CORE_BODY_IDS: readonly BodyId[] = BODY_IDS.filter((id) => BODIES[id].survey === 'core');
/** Bodies of the Extended Survey (transmitted separately after the core survey). */
export const EXTENDED_BODY_IDS: readonly BodyId[] = BODY_IDS.filter((id) => BODIES[id].survey === 'extended');

export function bodyById(id: BodyId): BodyDef {
  return BODIES[id];
}

export function isBodyId(x: unknown): x is BodyId {
  return typeof x === 'string' && (BODY_IDS as readonly string[]).includes(x);
}
