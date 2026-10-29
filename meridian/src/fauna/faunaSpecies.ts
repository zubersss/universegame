import type { BodyId } from '../world/bodies';
import type { SurfaceInfo } from '../world/surface';
import type { BehaviourParams } from './behaviour';
import { duneSledge, groveTrine, type FaunaGeometry } from './faunaMeshes';

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
];

export function faunaFor(body: BodyId): FaunaSpecies[] {
  return FAUNA.filter((s) => s.body === body);
}

export function faunaById(id: string): FaunaSpecies | undefined {
  return FAUNA.find((s) => s.id === id);
}
