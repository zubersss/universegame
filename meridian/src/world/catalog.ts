// Sol catalog: BodyDefs built from the scientific values in src/data/sol.json
// through the documented mapping in scale.ts. Scientific values stay in
// `real` (with per-field measured/estimated/fictional tags); everything else
// on a BodyDef is a gameplay value. Pure data: no Three.js (worker-safe).

import sol from '../data/sol.json';
import type { AtmosphereDef, BodyDef, BodyFrame, BodyKind, BodyPalette, CloudLayerDef, DataTag, Explore, RealData } from './bodies';
import { auToGame, eclipticToSystem, gameRadius, maxLevelFor, moonDistance, moonOffset, systemPosition } from './scale';

interface Tagged<T> {
  value: T;
  tag: DataTag;
  unit?: string;
}

interface SolBody {
  id: string;
  name: string;
  kind: 'star' | 'planet' | 'moon';
  parent: string | null;
  radiusKm: Tagged<number>;
  gravity: Tagged<number>;
  massKg: Tagged<number>;
  rotationHours: Tagged<number>;
  hasAtmosphere: Tagged<boolean>;
  positionKm: Tagged<number[]>;
  semiMajorAxisKm?: Tagged<number>;
  luminosityW?: Tagged<number>;
  effectiveTempK?: Tagged<number>;
  /** J2000-ecliptic unit vectors of the north pole and prime meridian at EPOCH. */
  orientation?: { north: number[]; primeMeridian: number[]; tag: DataTag; source: string };
  source: string;
  verified: boolean;
}

interface SolBelt {
  id: string;
  name: string;
  innerAu: Tagged<number>;
  outerAu: Tagged<number>;
  halfThicknessAu: Tagged<number>;
  note: string;
}

/** Gameplay presentation per Sol body: tuned values, not measurements. */
interface Look {
  explore: Explore;
  surface: 'procedural' | 'data';
  dataset?: string;
  power: string | null;
  atmosphereHeight: number;
  maxHeight: number;
  /** Ocean surface height above the datum [m] (gameplay), null without an ocean. */
  seaLevel?: number;
  /** Height above the datum of the zero elevation [m] (gameplay). */
  reliefZero?: number;
  atmosphere: AtmosphereDef | null;
  clouds: CloudLayerDef[];
  palette: BodyPalette;
  biomeNames: [string, string];
  description: string;
  fiction: string[];
}

const SCALE_FICTION = ['gameplay radius ÷ 40 and system distances compressed (scale.ts)', 'static at the catalog epoch'];

const airless = (palette: BodyPalette, rest: Omit<Look, 'atmosphere' | 'clouds' | 'atmosphereHeight' | 'palette'>): Look => ({
  ...rest,
  atmosphere: null,
  clouds: [],
  atmosphereHeight: 0,
  palette,
});

const LOOKS: Record<string, Look> = {
  sun: airless(
    { a1: 0xfff1d0, a2: 0xffd28a, a3: 0xffffff, b1: 0xffe2a8, b2: 0xffb460, b3: 0xfff8e8, special: 0xffffff, proxyNight: 0xffe2a8 },
    {
      explore: 'none', surface: 'procedural', power: null, maxHeight: 0,
      biomeNames: ['Photosphere', 'Granulation'],
      description: 'The star at the center of the system: navigable at a distance, no landing.',
      fiction: [...SCALE_FICTION, 'heat hazard is a gameplay rule'],
    },
  ),
  mercury: airless(
    { a1: 0x8f8579, a2: 0x6d655c, a3: 0xb0a698, b1: 0x7a736b, b2: 0x5c5650, b3: 0x9c9388, special: 0xd6d0c4, proxyNight: 0x060606 },
    {
      explore: 'surface', surface: 'procedural', power: 'sunline-dash', maxHeight: 2000, reliefZero: 500,
      biomeNames: ['Cratered Highlands', 'Smooth Plains'],
      description: 'The innermost planet: airless, cratered, scorched by day and frozen by night.',
      fiction: [...SCALE_FICTION, 'surface terrain is procedural', 'suit heat/cold shield'],
    },
  ),
  venus: {
    explore: 'surface', surface: 'procedural', power: 'pressure-glide', atmosphereHeight: 14000, maxHeight: 2600, reliefZero: 500,
    atmosphere: {
      rayleigh: [2.6e-5, 2.4e-5, 1.4e-5], rayleighH: 2600,
      mie: [1.9e-4, 1.6e-4, 8.0e-5], mieH: 2200, mieG: 0.72,
      sunIntensity: 20, airglow: [0.006, 0.004, 0.001],
    },
    // Closed sulphuric-acid deck (coverage above ~1.5 leaves no gaps): pale yellow, faint streaks.
    clouds: [{ altitude: 9000, thickness: 1800, coverage: 1.6, scale: 14000, speed: 0.00004, tint: [0.84, 0.72, 0.5], opacity: 1.0, streak: 0.6 }],
    palette: { a1: 0xa8865a, a2: 0x7d5e3c, a3: 0xc7a674, b1: 0x8c6a44, b2: 0x5e4630, b3: 0xb89466, special: 0x3a2a1c, proxyNight: 0x1a0e06 },
    biomeNames: ['Tessera Highlands', 'Volcanic Plains'],
    description: 'A runaway-greenhouse world under permanent sulfuric cloud, with crushing pressure at the ground.',
    fiction: [...SCALE_FICTION, 'surface terrain is procedural', 'suit pressure/heat shield', 'sky brightness tuned for play'],
  },
  earth: {
    // Datum 320 m below sea level: the gameplay sea floor bottoms out near -300 m (scale.ts relief ÷ 5, deep ocean compressed).
    explore: 'surface', surface: 'data', dataset: 'earth', power: 'skyborne-flight', atmosphereHeight: 8000, maxHeight: 2600, seaLevel: 320,
    atmosphere: {
      rayleigh: [2.7e-5, 6.3e-5, 1.56e-4], rayleighH: 1700,
      mie: [2.0e-5, 2.0e-5, 2.0e-5], mieH: 600, mieG: 0.76,
      sunIntensity: 22, airglow: [0.002, 0.005, 0.004],
    },
    clouds: [
      { altitude: 2200, thickness: 500, coverage: 0.45, scale: 6000, speed: 0.000012, tint: [1.0, 1.0, 1.0], opacity: 0.85, streak: 0.2 },
      { altitude: 5600, thickness: 300, coverage: 0.3, scale: 11000, speed: 0.00002, tint: [0.98, 0.99, 1.0], opacity: 0.5, streak: 0.85 },
    ],
    // A: dry ground (earth, dry grass/sand accent, rock); B: vegetation (green, darker under forest, rock); special: snow and ice.
    palette: { a1: 0x8a7a58, a2: 0x7a746a, a3: 0xb9a578, b1: 0x55703a, b2: 0x6a5f4c, b3: 0x8f9a58, special: 0xf4f7fa, proxyNight: 0x05080c },
    biomeNames: ['Uplands', 'Lowlands'],
    description: 'Home: oceans over 71% of the surface, continents shaped from real elevation data.',
    fiction: [
      ...SCALE_FICTION,
      'relief exaggerated 8× relative to the radius',
      'detail below the data resolution is procedural',
      'Southern Alps: relief above the global grid kept at 35% so slopes stay climbable',
    ],
  },
  moon: airless(
    { a1: 0x9a9893, a2: 0x7d7b77, a3: 0xb5b3ad, b1: 0x868480, b2: 0x7c7a76, b3: 0x8b8a86, special: 0xc8c6c0, proxyNight: 0x060606 },
    {
      // Real relief about -11 to +3 km (South Pole-Aitken floor to rims): gameplay /5 above a datum 2.4 km down.
      explore: 'surface', surface: 'procedural', power: 'lunar-step', maxHeight: 3200, reliefZero: 2400,
      biomeNames: ['Highlands', 'Maria'],
      description: "Earth's moon: bright cratered highlands and dark basaltic maria.",
      fiction: [...SCALE_FICTION, 'surface terrain is procedural'],
    },
  ),
  mars: {
    // Real relief about -9 to +25 km (Hellas floor to Olympus Mons over Tharsis): gameplay /5 above a datum 1.9 km down.
    explore: 'surface', surface: 'procedural', power: 'redline', atmosphereHeight: 6000, maxHeight: 7200, reliefZero: 1900,
    atmosphere: {
      rayleigh: [2.0e-6, 4.0e-6, 8.0e-6], rayleighH: 1300,
      // Suspended dust (vertical optical depth ~0.3 red, ~0.1 blue; real Mars 0.3-0.9) gives the butterscotch sky.
      mie: [2.6e-4, 1.6e-4, 9.0e-5], mieH: 1100, mieG: 0.74,
      sunIntensity: 24, airglow: [0.004, 0.002, 0.001],
    },
    clouds: [{ altitude: 3600, thickness: 300, coverage: 0.12, scale: 9000, speed: 0.00001, tint: [1.0, 0.92, 0.84], opacity: 0.35, streak: 0.8 }],
    // A: bright dusty ground (butterscotch), rock, pale dust; B: dark basaltic sand and rock.
    palette: { a1: 0xb8774a, a2: 0x8a553a, a3: 0xcf9a68, b1: 0x6f5544, b2: 0x5a463b, b3: 0x8a6c55, special: 0xe8e4dc, proxyNight: 0x120806 },
    biomeNames: ['Southern Highlands', 'Northern Lowlands'],
    description: 'A cold desert world of rust plains, giant volcanoes and canyon systems under a thin dusty sky.',
    fiction: [...SCALE_FICTION, 'surface terrain is procedural', 'sky density tuned for play'],
  },
  jupiter: {
    explore: 'zone', surface: 'procedural', power: 'storm-lift', atmosphereHeight: 20000, maxHeight: 50,
    atmosphere: {
      rayleigh: [1.2e-5, 2.0e-5, 3.2e-5], rayleighH: 3000,
      mie: [5.0e-5, 4.2e-5, 3.0e-5], mieH: 2500, mieG: 0.7,
      sunIntensity: 16, airglow: [0.004, 0.003, 0.002],
    },
    clouds: [], // the banded cloud deck is drawn by the proxy globe
    palette: { a1: 0xd8b48a, a2: 0xb07850, a3: 0xe8dcc8, b1: 0xc49a6c, b2: 0x8a5a3a, b3: 0xf0e6d6, special: 0xb04a2a, proxyNight: 0x0a0806 },
    biomeNames: ['Zones', 'Belts'],
    description: 'The largest planet: banded clouds of ammonia over a deep hydrogen atmosphere, no solid ground.',
    fiction: [...SCALE_FICTION, 'EVA zone and wind field are invented'],
  },
  europa: airless(
    { a1: 0xd8d2c4, a2: 0xbfb6a4, a3: 0xeee8dc, b1: 0xc4b49a, b2: 0x8a5a3a, b3: 0xe0d6c4, special: 0xa0623e, proxyNight: 0x070708 },
    {
      explore: 'surface', surface: 'procedural', power: 'anchor-blink', maxHeight: 1000, reliefZero: 450,
      biomeNames: ['Ridged Plains', 'Chaos Terrain'],
      description: "Jupiter's ice moon: a cracked water-ice shell over a subsurface ocean.",
      fiction: [...SCALE_FICTION, 'surface terrain is procedural'],
    },
  ),
  saturn: {
    explore: 'zone', surface: 'procedural', power: 'ring-skate', atmosphereHeight: 20000, maxHeight: 50,
    atmosphere: {
      rayleigh: [1.4e-5, 2.0e-5, 2.8e-5], rayleighH: 3200,
      mie: [5.0e-5, 4.6e-5, 3.4e-5], mieH: 2600, mieG: 0.7,
      sunIntensity: 15, airglow: [0.003, 0.003, 0.002],
    },
    clouds: [], // the banded cloud deck is drawn by the proxy globe
    palette: { a1: 0xe0c890, a2: 0xc8aa70, a3: 0xf0e4c4, b1: 0xd4b880, b2: 0xb09060, b3: 0xf4ead4, special: 0xc8b07a, proxyNight: 0x0a0906 },
    biomeNames: ['Zones', 'Belts'],
    description: 'The ringed giant: pale golden cloud bands and a vast, thin ring system of ice.',
    fiction: [...SCALE_FICTION, 'ring-plane platform zone is invented'],
  },
  titan: {
    explore: 'surface', surface: 'procedural', power: 'wing-glide', atmosphereHeight: 14000, maxHeight: 1000, reliefZero: 450,
    atmosphere: {
      rayleigh: [5.0e-6, 6.0e-6, 8.0e-6], rayleighH: 2500,
      mie: [1.2e-4, 6.0e-5, 1.5e-5], mieH: 2400, mieG: 0.68,
      sunIntensity: 14, airglow: [0.004, 0.002, 0.0005],
    },
    clouds: [{ altitude: 7000, thickness: 1200, coverage: 0.35, scale: 12000, speed: 0.00002, tint: [1.0, 0.8, 0.5], opacity: 0.6, streak: 0.6 }],
    palette: { a1: 0x9a7a4a, a2: 0x6b4a2a, a3: 0xb89a66, b1: 0x5a3e22, b2: 0x4a3420, b3: 0x8a6a40, special: 0x1a1410, proxyNight: 0x0c0804 },
    biomeNames: ['Bright Uplands', 'Dark Dune Fields'],
    description: "Saturn's largest moon: a dense orange nitrogen haze over dunes and methane lakes.",
    fiction: [...SCALE_FICTION, 'surface terrain is procedural'],
  },
  uranus: {
    explore: 'zone', surface: 'procedural', power: 'cold-drift', atmosphereHeight: 20000, maxHeight: 50,
    atmosphere: {
      rayleigh: [1.0e-5, 4.0e-5, 4.5e-5], rayleighH: 3000,
      mie: [1.5e-5, 2.0e-5, 2.0e-5], mieH: 2400, mieG: 0.72,
      sunIntensity: 13, airglow: [0.001, 0.003, 0.003],
    },
    clouds: [], // the banded cloud deck is drawn by the proxy globe
    palette: { a1: 0x9fd8e0, a2: 0x86c4cc, a3: 0xc4ecf0, b1: 0x94d0d8, b2: 0x7ab8c0, b3: 0xd0f0f4, special: 0xe0f8fa, proxyNight: 0x050a0b },
    biomeNames: ['Haze', 'Bands'],
    description: 'A pale cyan ice giant tipped on its side, its methane haze almost featureless.',
    fiction: [...SCALE_FICTION, 'EVA zone and crystal clouds are invented'],
  },
  neptune: {
    explore: 'zone', surface: 'procedural', power: 'gale-rider', atmosphereHeight: 20000, maxHeight: 50,
    atmosphere: {
      rayleigh: [6.0e-6, 2.4e-5, 6.0e-5], rayleighH: 3000,
      mie: [1.5e-5, 1.8e-5, 2.4e-5], mieH: 2400, mieG: 0.72,
      sunIntensity: 12, airglow: [0.001, 0.002, 0.004],
    },
    clouds: [], // the banded cloud deck is drawn by the proxy globe
    palette: { a1: 0x3f62c8, a2: 0x2e4aa0, a3: 0x7a9ae0, b1: 0x3656b4, b2: 0x24408c, b3: 0xa8bcf0, special: 0xe8eeff, proxyNight: 0x03050c },
    biomeNames: ['Bands', 'Storms'],
    description: 'The outermost giant: deep blue methane skies and the fastest winds in the system.',
    fiction: [...SCALE_FICTION, 'EVA zone and jet-band wind field are invented'],
  },
};

function tagsOf(b: SolBody): Record<string, DataTag> {
  const t: Record<string, DataTag> = {
    radiusKm: b.radiusKm.tag,
    gravity: b.gravity.tag,
    massKg: b.massKg.tag,
    rotationHours: b.rotationHours.tag,
    positionKm: b.positionKm.tag,
  };
  if (b.semiMajorAxisKm) t.semiMajorAxisKm = b.semiMajorAxisKm.tag;
  if (b.luminosityW) t.luminosityW = b.luminosityW.tag;
  if (b.effectiveTempK) t.effectiveTempK = b.effectiveTempK.tag;
  return t;
}

const solBodies = sol.bodies as SolBody[];
const solById = new Map(solBodies.map((b) => [b.id, b]));

/** Default frame (system +Y north, +X prime meridian), used where no orientation is known. */
export const DEFAULT_FRAME: BodyFrame = { north: [0, 1, 0], meridian: [1, 0, 0], east: [0, 0, -1], tag: 'fictional' };

/** Body frame in the game's system axes from the catalog orientation (ecliptic unit vectors). */
function frameOf(b: SolBody): BodyFrame {
  const o = b.orientation;
  if (!o) return DEFAULT_FRAME;
  // Gram-Schmidt: the catalog vectors are rounded to 12 decimals.
  const nr = eclipticToSystem(o.north, 1);
  const nl = Math.hypot(nr[0], nr[1], nr[2]);
  const north: [number, number, number] = [nr[0] / nl, nr[1] / nl, nr[2] / nl];
  const mr = eclipticToSystem(o.primeMeridian, 1);
  const md = mr[0] * north[0] + mr[1] * north[1] + mr[2] * north[2];
  const mo = [mr[0] - md * north[0], mr[1] - md * north[1], mr[2] - md * north[2]];
  const ml = Math.hypot(mo[0], mo[1], mo[2]);
  const meridian: [number, number, number] = [mo[0] / ml, mo[1] / ml, mo[2] / ml];
  const east: [number, number, number] = [
    north[1] * meridian[2] - north[2] * meridian[1],
    north[2] * meridian[0] - north[0] * meridian[2],
    north[0] * meridian[1] - north[1] * meridian[0],
  ];
  return { north, meridian, east, tag: o.tag };
}

function centerOf(b: SolBody): [number, number, number] {
  if (!b.parent || b.kind !== 'moon') return systemPosition(b.positionKm.value);
  const p = solById.get(b.parent)!;
  const pc = systemPosition(p.positionKm.value);
  const rel = [0, 1, 2].map((i) => b.positionKm.value[i] - p.positionKm.value[i]);
  const off = moonOffset(rel, p.radiusKm.value, gameRadius(p.radiusKm.value), gameRadius(b.radiusKm.value));
  return [pc[0] + off[0], pc[1] + off[1], pc[2] + off[2]];
}

/** Sol BodyDefs in catalog order; `seedFor` is supplied by bodies.ts (determinism key). */
export function buildSolBodies(seedFor: (id: string) => number, firstIndex: number): BodyDef[] {
  return solBodies.map((b, i) => {
    const look = LOOKS[b.id];
    if (!look) throw new Error(`No gameplay look for catalog body ${b.id}`);
    const radius = gameRadius(b.radiusKm.value);
    const fiction = [...look.fiction];
    let positionSource: string = sol.sources.positions.url;
    if (b.kind === 'moon' && b.parent) {
      const p = solById.get(b.parent)!;
      const rel = [0, 1, 2].map((i) => b.positionKm.value[i] - p.positionKm.value[i]);
      const { rule } = moonDistance(Math.hypot(rel[0], rel[1], rel[2]), p.radiusKm.value, gameRadius(p.radiusKm.value), radius);
      fiction.push(rule === 'sqrt'
        ? `distance from ${p.name} compressed (square-root rule)`
        : `distance from ${p.name} set by the minimum separation (4.5 x the sum of the gameplay radii)`);
    }
    if (b.positionKm.tag === 'fictional') {
      fiction.push('direction from its parent invented (no ephemeris yet)');
      positionSource = 'fictional: direction invented until an ephemeris is available';
    }
    const real: RealData = {
      radiusKm: b.radiusKm.value,
      gravity: b.gravity.value,
      massKg: b.massKg.value,
      rotationHours: b.rotationHours.value,
      positionKm: b.positionKm.value as [number, number, number],
      luminosityW: b.luminosityW?.value,
      effectiveTempK: b.effectiveTempK?.value,
      tags: tagsOf(b),
      source: b.source,
      positionSource,
      verified: b.verified,
    };
    const kind: BodyKind = b.kind;
    return {
      id: b.id,
      index: firstIndex + i,
      name: b.name,
      system: 'sol',
      kind,
      parent: b.parent,
      explore: look.explore,
      real,
      center: centerOf(b),
      frame: frameOf(b),
      radius,
      atmosphereHeight: look.atmosphereHeight,
      gravity: b.gravity.value,
      maxHeight: look.maxHeight,
      maxLevel: maxLevelFor(radius),
      seed: seedFor(b.id),
      seaLevel: look.seaLevel ?? null,
      reliefZero: look.reliefZero,
      surface: look.surface,
      dataset: look.dataset,
      power: look.power,
      fiction,
      atmosphere: look.atmosphere,
      clouds: look.clouds,
      palette: look.palette,
      biomeNames: look.biomeNames,
      description: look.description,
    } satisfies BodyDef;
  });
}

export interface BeltDef {
  id: string;
  name: string;
  /** Gameplay radii from the Sun in the ecliptic plane [m]. */
  inner: number;
  outer: number;
  /** Gameplay half-thickness above and below the ecliptic plane [m]. */
  halfThickness: number;
  real: { innerAu: number; outerAu: number; halfThicknessAu: number; tag: DataTag; note: string; source: string };
}

export const BELTS: readonly BeltDef[] = (sol.belts as SolBelt[]).map((b) => ({
  id: b.id,
  name: b.name,
  inner: auToGame(b.innerAu.value),
  outer: auToGame(b.outerAu.value),
  halfThickness: auToGame(b.halfThicknessAu.value),
  real: {
    innerAu: b.innerAu.value,
    outerAu: b.outerAu.value,
    halfThicknessAu: b.halfThicknessAu.value,
    tag: b.innerAu.tag,
    note: b.note,
    source: sol.sources.belts.note,
  },
}));

/** Data provenance for the journal and tests. */
export const SOL_EPOCH = sol.epoch;
export const SOL_SOURCES = sol.sources;
