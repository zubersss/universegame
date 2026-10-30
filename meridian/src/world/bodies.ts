// Celestial body definitions. Pure data: this module is shared by the main
// thread and the terrain worker, so it must not import Three.js.
// All distances are meters in system coordinates (right-handed).
// The catalog holds every system's bodies (Sol from src/data/sol.json via
// catalog.ts, the fictional Quiet System below); `BODY_IDS` is the set the
// game currently plays and iterates (travel, gravity, proxies).

import { hashCombine } from '../core/rng';
import { BELTS, DEFAULT_FRAME, buildSolBodies } from './catalog';

export { DEFAULT_FRAME };
import { maxLevelFor } from './scale';
import type { ZoneDef } from './zones';

/** Catalog key, e.g. 'earth', 'ilex'. Validate untrusted input with isBodyId. */
export type BodyId = string;
export type SystemId = 'sol' | 'proxima' | 'quiet';
export type BodyKind = 'star' | 'planet' | 'moon';
export type Explore = 'surface' | 'zone' | 'none';
export type DataTag = 'measured' | 'estimated' | 'fictional';

/** The bodies the game plays now (the Quiet System until LEAD switches travel to Sol in L7). */
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

/**
 * Body-fixed axes in the system frame (unit vectors): north pole, prime
 * meridian (latitude 0, longitude 0) and east = north × meridian. Bodies do
 * not rotate in play; the frame is their orientation at EPOCH where known.
 */
export interface BodyFrame {
  north: [number, number, number];
  meridian: [number, number, number];
  east: [number, number, number];
  tag: DataTag;
}

/** Scientific values (never gameplay-scaled); `tags` labels each field. */
export interface RealData {
  radiusKm: number;
  /** Surface gravity [m/s²]. */
  gravity: number;
  massKg: number;
  /** Sidereal rotation [h], negative = retrograde. Informational: bodies do not rotate in play. */
  rotationHours: number;
  /** Heliocentric J2000-ecliptic position at EPOCH [km]. */
  positionKm: [number, number, number];
  /** Stars only. */
  luminosityW?: number;
  effectiveTempK?: number;
  tags: Record<string, DataTag>;
  /** Source of the physical values ('pending (...)' until verified). */
  source: string;
  positionSource: string;
  verified: boolean;
}

export interface BodyDef {
  id: BodyId;
  index: number;
  name: string;
  system: SystemId;
  kind: BodyKind;
  /** Parent body for moons, else null (or the star). */
  parent: BodyId | null;
  explore: Explore;
  /** Scientific values; null for fictional bodies. */
  real: RealData | null;
  /** Gameplay center [m, system frame]. */
  center: [number, number, number];
  /** Body-fixed orientation (latitude/longitude axes) in the system frame. */
  frame: BodyFrame;
  radius: number;
  atmosphereHeight: number;
  gravity: number;
  maxHeight: number;
  /** Contact/max-detail quadtree level: ceil(log2(2R/128)). */
  maxLevel: number;
  seed: number;
  /** Height above the datum [m] of the ocean surface, or null for bodies without an ocean. */
  seaLevel: number | null;
  /** 'data' bodies sample a dataset for the large-scale layer and use the seed only for infill. */
  surface: 'procedural' | 'data';
  dataset?: string;
  zone?: ZoneDef;
  /** Ability id active while exploring this body (PLAYER's AbilityId), null where nobody leaves the ship. */
  power: string | null;
  /** Which aspects of this body are invented for gameplay. */
  fiction: string[];
  atmosphere: AtmosphereDef | null;
  clouds: CloudLayerDef[];
  palette: BodyPalette;
  biomeNames: [string, string];
  description: string;
}

function seedFor(id: BodyId): number {
  return hashCombine(WORLD_SEED, GENERATOR_VERSION, id);
}

const QUIET = {
  system: 'quiet',
  parent: null,
  frame: DEFAULT_FRAME,
  seaLevel: null,
  explore: 'surface',
  real: null,
  surface: 'procedural',
  power: 'walk',
  fiction: ['the whole Quiet System is fictional'],
} as const satisfies Partial<BodyDef>;

const QUIET_BODIES: Record<string, BodyDef> = {
  ilex: {
    ...QUIET,
    fiction: [...QUIET.fiction],
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
    ...QUIET,
    fiction: [...QUIET.fiction],
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
    ...QUIET,
    fiction: [...QUIET.fiction],
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

const SOL_BODIES = buildSolBodies(seedFor, Object.keys(QUIET_BODIES).length);

/** Every catalog body by id (all systems). */
export const BODIES: Record<BodyId, BodyDef> = { ...QUIET_BODIES, ...Object.fromEntries(SOL_BODIES.map((b) => [b.id, b])) };

/** Catalog ids per system, in catalog order. */
export const SYSTEM_BODY_IDS: Record<SystemId, readonly BodyId[]> = {
  quiet: Object.keys(QUIET_BODIES),
  sol: SOL_BODIES.map((b) => b.id),
  proxima: [],
};

/** Sol travel order outward from the Sun, with belt bands (from catalog.BELTS) between the bodies. */
export const SOL_TRAVEL_ORDER: readonly ({ body: BodyId } | { belt: string })[] = [
  { body: 'sun' }, { body: 'mercury' }, { body: 'venus' }, { body: 'earth' }, { body: 'moon' }, { body: 'mars' },
  { belt: 'asteroid-belt' }, { body: 'jupiter' }, { body: 'europa' }, { body: 'saturn' }, { body: 'titan' },
  { body: 'uranus' }, { body: 'neptune' }, { belt: 'kuiper-belt' },
];

/**
 * Largest gameplay distance from the system origin that play can reach [m]:
 * the outer edge of the outermost belt (or the farthest body) plus 10%.
 */
export const SYSTEM_EXTENT: number = (() => {
  let m = 0;
  for (const b of Object.values(BODIES)) m = Math.max(m, Math.hypot(...b.center) + b.radius + b.atmosphereHeight);
  for (const b of BELTS) m = Math.max(m, b.outer);
  return m * 1.1;
})();

export function bodyById(id: BodyId): BodyDef {
  const d = BODIES[id];
  if (!d) throw new Error(`Unknown body ${id}`);
  return d;
}

/** True for any catalog id (checks the catalog, not a literal list). */
export function isBodyId(x: unknown): x is BodyId {
  return typeof x === 'string' && Object.prototype.hasOwnProperty.call(BODIES, x);
}

/** Unit direction from a body's center toward its star (light direction). Quiet System: the fixed SUN_DIR. */
export function sunDirFor(def: BodyDef): [number, number, number] {
  if (def.system === 'quiet') return [SUN_DIR[0], SUN_DIR[1], SUN_DIR[2]];
  const c = def.center;
  const l = Math.hypot(c[0], c[1], c[2]);
  return l > 0 ? [-c[0] / l, -c[1] / l, -c[2] / l] : [SUN_DIR[0], SUN_DIR[1], SUN_DIR[2]];
}
