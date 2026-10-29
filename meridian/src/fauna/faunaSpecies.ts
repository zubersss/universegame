import type { BodyId } from '../world/bodies';
import type { SurfaceInfo } from '../world/surface';
import type { BehaviourParams } from './behaviour';
import {
  brineSkater, chalkSkein, columnDrifter, crustTilter, duneSledge, fogWader, glassTick, groveTrine, mesaKite, mossCreeper, ochreSounder, saltVeil,
  type FaunaGeometry,
} from './faunaMeshes';

export interface FaunaSpecies {
  /** `${body}-${name}`; shares the journal namespace with flora/minerals. */
  id: string;
  body: BodyId;
  name: string;
  /** Journal field notes shown when scanned. */
  description: string;
  make: () => FaunaGeometry;
  roughness: number;
  /** Instance height range (m). */
  hMin: number;
  hMax: number;
  /** Herd candidates per spawn cell. */
  candidates: number;
  /** Probability that a candidate herd exists, from the surface at its home point. */
  habitat: (s: SurfaceInfo, slope: number) => number;
  maxSlope: number;
  /** Herd size range. */
  groupMin: number;
  groupMax: number;
  behaviour: BehaviourParams;
  /** Gait stride length (m per full cycle at instance height 1). */
  stride: number;
  /** Gait shape: phase step between legs (rad), foot lift, foot swing and body bob (unit-height fractions). */
  gait: { legStep: number; lift: number; swing: number; bob: number };
  /** Fliers and floaters: cruise height above the ground (m) and a slow vertical bob (m). */
  hover?: { height: number; bob: number };
  /** Burrowers sink out of sight while alert or fleeing and resurface when calm. */
  burrows?: boolean;
  /** Scanner aim radius as a fraction of instance height. */
  scanRadius: number;
  /** LOD0 distance and max render distance (m) at Balanced. */
  lod0: number;
  range: number;
}

const sat = (x: number) => (x < 0 ? 0 : x > 1 ? 1 : x);
const ss = (a: number, b: number, x: number) => {
  const t = sat((x - a) / (b - a));
  return t * t * (3 - 2 * t);
};

// Append new species at the end: the index is not part of any ID, but keeping
// order stable keeps diffs readable.
export const FAUNA: FaunaSpecies[] = [
  {
    id: 'ilex-trine', body: 'ilex', name: 'Grove trine',
    description:
      'A tripedal grazer that browses the margins of the lantern groves, its pale carapace held level on three jointed stilts. ' +
      'It feeds on the teal loam through a single hanging proboscis and stops to watch anything that approaches, then withdraws in long, unhurried strides. ' +
      'Its dorsal vanes match the colour of the grove canopy almost exactly.',
    make: groveTrine, roughness: 0.7, hMin: 1.9, hMax: 2.7, candidates: 4,
    // Grove edges: where the teal loam thins out into open ochre ground, in the lowlands.
    habitat: (s, slope) => (ss(0.05, 0.3, s.special) * (1 - ss(0.55, 0.85, s.special)) * ss(0.3, 0.6, s.biome) * 0.9 + 0.06 * s.biome) * (slope < 0.25 ? 1 : 0),
    maxSlope: 0.25, groupMin: 2, groupMax: 5,
    behaviour: {
      walkSpeed: 0.9, fleeSpeed: 3.4, turnRate: 1.1, homeRadius: 22,
      alertRadius: 26, fleeRadius: 9, shipFleeRadius: 140,
      idleMin: 3, idleMax: 9, callRate: 0.02,
    },
    stride: 1.4, gait: { legStep: (Math.PI * 2) / 3, lift: 0.09, swing: 0.13, bob: 0.022 },
    scanRadius: 0.32, lod0: 70, range: 380,
  },
  {
    id: 'vesper-sledge', body: 'vesper', name: 'Dune sledge',
    description:
      'A broad, low grazer armoured in overlapping oxide-red plates, hauling itself over the dune crests on two heavy forelimbs while its rear drags behind. ' +
      'It leaves a ribbed track that the wind erases within the hour. It approaches observers to a fixed distance, then waits.',
    make: duneSledge, roughness: 0.85, hMin: 1.0, hMax: 1.4, candidates: 4,
    // The pale dune sea, away from the black glass, on gentle slopes.
    habitat: (s, slope) => (ss(0.4, 0.8, s.biome) * (1 - ss(0.3, 0.6, s.special)) * 0.6 + 0.04 * s.biome) * (slope < 0.3 ? 1 : 0),
    maxSlope: 0.3, groupMin: 3, groupMax: 6,
    behaviour: {
      walkSpeed: 0.7, fleeSpeed: 2.6, turnRate: 0.8, homeRadius: 30,
      alertRadius: 32, fleeRadius: 6, shipFleeRadius: 180,
      idleMin: 4, idleMax: 12, callRate: 0.015, curiousDistance: 15,
    },
    stride: 1.6, gait: { legStep: Math.PI, lift: 0.07, swing: 0.2, bob: 0.03 },
    scanRadius: 0.45, lod0: 80, range: 420,
  },
  // ------------------------------------------------------------- Ilex
  {
    id: 'ilex-skein', body: 'ilex', name: 'Chalk skein',
    description:
      'Thin, pale gliders no heavier than paper, riding the updrafts that rise along the chalk ridges. ' +
      'They move as a loose sheet, each keeping a fixed distance from its neighbours. When disturbed the sheet tears upward and reforms some way off.',
    make: chalkSkein, roughness: 0.9, hMin: 0.35, hMax: 0.5, candidates: 2,
    habitat: (s) => 0.5 * ss(0.3, 0.7, s.rockiness) + 0.04 * (1 - s.biome),
    maxSlope: 0.9, groupMin: 6, groupMax: 12,
    behaviour: {
      walkSpeed: 3.5, fleeSpeed: 7, turnRate: 1.4, homeRadius: 35,
      alertRadius: 0, fleeRadius: 12, shipFleeRadius: 160,
      idleMin: 0.5, idleMax: 1.5, callRate: 0.03,
    },
    stride: 6, gait: { legStep: Math.PI, lift: 0, swing: 0, bob: 0.05 },
    hover: { height: 16, bob: 3 },
    scanRadius: 1.2, lod0: 80, range: 420,
  },
  {
    id: 'ilex-sounder', body: 'ilex', name: 'Ochre sounder',
    description:
      'A flattened burrower that lies just under the ochre crust, surfacing only to raise a ring of fine tendrils into the wind. ' +
      'It senses footsteps through the ground long before it can see anything. Most observations end with a soft collapse of sand and an empty ring.',
    make: ochreSounder, roughness: 0.95, hMin: 0.5, hMax: 0.8, candidates: 2,
    habitat: (s, slope) => 0.35 * ss(0.4, 0.8, s.biome) * (1 - ss(0.1, 0.4, s.special)) * (slope < 0.2 ? 1 : 0),
    maxSlope: 0.2, groupMin: 1, groupMax: 1,
    behaviour: {
      walkSpeed: 0, fleeSpeed: 0, turnRate: 0.5, homeRadius: 1,
      alertRadius: 30, fleeRadius: 18, shipFleeRadius: 250,
      idleMin: 10, idleMax: 30, callRate: 0.01,
    },
    stride: 1, gait: { legStep: Math.PI, lift: 0, swing: 0, bob: 0 },
    burrows: true,
    scanRadius: 0.9, lod0: 60, range: 260,
  },
  // ----------------------------------------------------------- Vesper
  {
    id: 'vesper-kite', body: 'vesper', name: 'Mesa kite',
    description:
      'A long-winged glider that circles the mesa rims on rising heat for most of the day. ' +
      'It descends only to rest on the caps of hoodoos and has never been seen over the dunes.',
    make: mesaKite, roughness: 0.85, hMin: 2.2, hMax: 2.8, candidates: 1,
    habitat: (s) => 0.5 * (1 - s.biome),
    maxSlope: 1, groupMin: 1, groupMax: 2,
    behaviour: {
      walkSpeed: 6, fleeSpeed: 9, turnRate: 0.5, homeRadius: 70,
      alertRadius: 0, fleeRadius: 0, shipFleeRadius: 120,
      idleMin: 0, idleMax: 0.2, callRate: 0.02,
    },
    stride: 20, gait: { legStep: Math.PI, lift: 0, swing: 0, bob: 0.02 },
    hover: { height: 30, bob: 4 },
    scanRadius: 0.5, lod0: 120, range: 520,
  },
  {
    id: 'vesper-tick', body: 'vesper', name: 'Glass tick',
    description:
      'Small crawlers with black, glassy shells, gathered in hundreds on the faces of the black glass outcrops. ' +
      'Disturbed, the colony spreads outward in a single ripple and slowly draws back together. Their shells are nearly indistinguishable from the mineral they live on.',
    make: glassTick, roughness: 0.15, hMin: 0.06, hMax: 0.09, candidates: 3,
    habitat: (s) => 0.8 * ss(0.4, 0.75, s.special),
    maxSlope: 0.6, groupMin: 14, groupMax: 24,
    behaviour: {
      walkSpeed: 0.15, fleeSpeed: 0.8, turnRate: 3, homeRadius: 3,
      alertRadius: 0, fleeRadius: 3, shipFleeRadius: 60,
      idleMin: 1, idleMax: 4, callRate: 0.01,
    },
    stride: 0.03, gait: { legStep: (Math.PI * 2) / 3, lift: 0.15, swing: 0.15, bob: 0.02 },
    scanRadius: 6, lod0: 25, range: 60,
  },
  // ------------------------------------------------------------ Orrin
  {
    id: 'orrin-wader', body: 'orrin', name: 'Fog wader',
    description:
      'A tall, narrow biped that feeds in the valley shallows with its head held low inside the fog layer. In clear air it appears to stand headless. ' +
      'It leaves in long, unhurried strides when approached and calls once before it goes.',
    make: fogWader, roughness: 0.8, hMin: 2.5, hMax: 3.2, candidates: 4,
    habitat: (s, slope) => (0.6 * ss(0.3, 0.7, s.special) + 0.03 * s.biome) * (slope < 0.25 ? 1 : 0),
    maxSlope: 0.25, groupMin: 2, groupMax: 4,
    behaviour: {
      walkSpeed: 0.8, fleeSpeed: 3.6, turnRate: 0.9, homeRadius: 26,
      alertRadius: 28, fleeRadius: 11, shipFleeRadius: 150,
      idleMin: 4, idleMax: 10, callRate: 0.02,
    },
    stride: 1.3, gait: { legStep: Math.PI, lift: 0.07, swing: 0.16, bob: 0.02 },
    scanRadius: 0.22, lod0: 80, range: 420,
  },
  {
    id: 'orrin-drifter', body: 'orrin', name: 'Column drifter',
    description:
      'A gas-filled body trailing long fine filaments, drifting between the basalt columns well above the ground. ' +
      'It shows no response to observers. Its filaments draw faint lines through the fog where they touch it.',
    make: columnDrifter, roughness: 0.5, hMin: 2.5, hMax: 3.5, candidates: 2,
    habitat: (s) => 0.4 * ss(0.15, 0.5, s.rockiness) + 0.06 * s.biome,
    maxSlope: 1, groupMin: 1, groupMax: 1,
    behaviour: {
      walkSpeed: 0.4, fleeSpeed: 0.8, turnRate: 0.2, homeRadius: 40,
      alertRadius: 0, fleeRadius: 0, shipFleeRadius: 90,
      idleMin: 2, idleMax: 6, callRate: 0.01,
    },
    stride: 4, gait: { legStep: Math.PI, lift: 0, swing: 0, bob: 0.01 },
    hover: { height: 14, bob: 2 },
    scanRadius: 0.35, lod0: 100, range: 480,
  },
  {
    id: 'orrin-creeper', body: 'orrin', name: 'Moss creeper',
    description:
      'Small, many-legged grazers that cross the moss in single file, each following the scent of the one ahead. ' +
      'When one stops, the whole line stops.',
    make: mossCreeper, roughness: 0.85, hMin: 0.2, hMax: 0.3, candidates: 3,
    habitat: (s, slope) => 0.5 * ss(0.5, 0.85, s.biome) * (1 - ss(0.3, 0.6, s.special)) * (slope < 0.35 ? 1 : 0),
    maxSlope: 0.35, groupMin: 5, groupMax: 10,
    behaviour: {
      walkSpeed: 0.35, fleeSpeed: 0.9, turnRate: 1.5, homeRadius: 8,
      alertRadius: 6, fleeRadius: 2.5, shipFleeRadius: 80,
      idleMin: 2, idleMax: 6, callRate: 0.005,
    },
    stride: 0.4, gait: { legStep: (Math.PI * 2) / 3, lift: 0.12, swing: 0.15, bob: 0.03 },
    scanRadius: 2.5, lod0: 30, range: 90,
  },
  // ------------------------------------------------------------- Saro
  {
    id: 'saro-skater', body: 'saro', name: 'Brine skater',
    description:
      'A flat, many-legged animal that skims the surface film of the brine pans without breaking it. ' +
      'Groups move together and scatter in all directions at once.',
    make: brineSkater, roughness: 0.4, hMin: 0.35, hMax: 0.5, candidates: 4,
    habitat: (s) => 0.7 * ss(0.3, 0.8, s.special) + 0.05 * s.biome,
    maxSlope: 0.3, groupMin: 6, groupMax: 12,
    behaviour: {
      walkSpeed: 1.2, fleeSpeed: 5, turnRate: 3, homeRadius: 15,
      alertRadius: 14, fleeRadius: 8, shipFleeRadius: 150,
      idleMin: 0.5, idleMax: 3, callRate: 0.005,
    },
    stride: 0.6, gait: { legStep: (Math.PI * 2) / 3, lift: 0.05, swing: 0.1, bob: 0.01 },
    scanRadius: 1.4, lod0: 50, range: 260,
  },
  {
    id: 'saro-tilter', body: 'saro', name: 'Crust tilter',
    description:
      'A solitary animal that stands motionless for hours, turning a broad, mirror-bright dorsal plate to follow the sun. ' +
      'The plate appears to regulate its temperature. It walks away when approached, slowly and without looking back.',
    make: crustTilter, roughness: 0.3, hMin: 1.3, hMax: 1.7, candidates: 2,
    habitat: (s, slope) => (0.25 * (1 - s.biome) + 0.3 * ss(0.2, 0.5, s.rockiness)) * (slope < 0.3 ? 1 : 0),
    maxSlope: 0.3, groupMin: 1, groupMax: 1,
    behaviour: {
      walkSpeed: 0.5, fleeSpeed: 1.1, turnRate: 0.5, homeRadius: 12,
      alertRadius: 0, fleeRadius: 14, shipFleeRadius: 120,
      idleMin: 20, idleMax: 60, callRate: 0.01,
    },
    stride: 1.2, gait: { legStep: Math.PI, lift: 0.06, swing: 0.1, bob: 0.01 },
    scanRadius: 0.5, lod0: 90, range: 420,
  },
  {
    id: 'saro-veil', body: 'saro', name: 'Salt veil',
    description:
      'Columns of minute translucent fliers that rise above the warm brine at midday. ' +
      'From a distance the column reads as a heat shimmer; only close up do individual animals resolve.',
    make: saltVeil, roughness: 0.6, hMin: 0.05, hMax: 0.08, candidates: 1,
    habitat: (s) => 0.6 * ss(0.4, 0.8, s.special),
    maxSlope: 1, groupMin: 24, groupMax: 40,
    behaviour: {
      walkSpeed: 0.8, fleeSpeed: 2, turnRate: 4, homeRadius: 3,
      alertRadius: 0, fleeRadius: 4, shipFleeRadius: 100,
      idleMin: 0, idleMax: 0.5, callRate: 0.005,
    },
    stride: 0.3, gait: { legStep: Math.PI, lift: 0, swing: 0, bob: 0 },
    hover: { height: 4, bob: 2.5 },
    scanRadius: 40, lod0: 30, range: 120,
  },
];

export function faunaFor(body: BodyId): FaunaSpecies[] {
  return FAUNA.filter((s) => s.body === body);
}

export function faunaById(id: string): FaunaSpecies | undefined {
  return FAUNA.find((s) => s.id === id);
}
