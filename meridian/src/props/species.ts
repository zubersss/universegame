import type { BodyId } from '../world/bodies';
import type { SurfaceInfo } from '../world/surface';
import {
  blackGlass, chalkSpire, duneBristle, fanShrub, lanternTree, pebbles, rimeShard, rustPillar, silverBoulder,
  type SpeciesGeometry,
  broadleaf,
  conifer,
  earthBoulder,
  lunarBoulder,
  lunarPebbles,
  marsBasalt,
  marsPebbles,
} from './propMeshes';

export type ColliderSpec =
  | { type: 'capsule'; radius: number; halfHeight: number; y: number } // all in units of instance height
  | { type: 'ball'; radius: number; y: number }
  | null;

export interface Species {
  id: string;
  body: BodyId;
  name: string;
  /** Journal text shown when scanned. */
  description: string;
  make: () => SpeciesGeometry;
  roughness: number;
  metalness: number;
  emissive?: number;
  /** Instance height range (m). */
  hMin: number;
  hMax: number;
  /** Candidates per placement cell. */
  candidates: number;
  /** Acceptance probability from surface info and slope (0..1 slope = 1 - n·up). */
  density: (s: SurfaceInfo, slope: number) => number;
  /** Max slope (1 - n·up) for placement. */
  maxSlope: number;
  /** How far the base sinks into the ground (fraction of height). */
  sink: number;
  /** Tilt toward the surface normal (0 = radial up, 1 = normal). */
  tiltToNormal: number;
  /** LOD0 and max render distance (m) at Balanced. */
  lod0: number;
  range: number;
  wind: number;
  castShadow: boolean;
  collider: ColliderSpec;
  /** Scannable natural object (journal entry). */
  scannable: boolean;
  /** Scanner aim radius around the base-to-top axis, as a fraction of instance height. */
  scanRadius: number;
}

const sat = (x: number) => (x < 0 ? 0 : x > 1 ? 1 : x);
const ss = (a: number, b: number, x: number) => {
  const t = sat((x - a) / (b - a));
  return t * t * (3 - 2 * t);
};

/**
 * Earth forest weight from the land-cover attributes (biome = vegetated share,
 * variation = forest or sand share, so both high = forest), below the treeline
 * (~2,300 m real; gameplay height = 320 + real / 5) and off snow and bare rock.
 */
function earthForest(s: SurfaceInfo): number {
  return ss(0.5, 0.8, s.biome) * ss(0.5, 0.72, s.variation) * (1 - ss(0.1, 0.4, s.special)) * (1 - ss(0.55, 0.85, s.rockiness)) * (1 - ss(700, 800, s.height));
}

export const SPECIES: Species[] = [
  // ------------------------------------------------------------- Ilex
  {
    id: 'ilex-lantern', body: 'ilex', name: 'Lantern-tree',
    description: 'Tall curved trunks carrying layered teal canopies. They grow only in dense groves, where their shade darkens the loam beneath.',
    make: lanternTree, roughness: 0.82, metalness: 0, hMin: 7, hMax: 14, candidates: 24,
    density: (s, slope) => ss(0.3, 0.7, s.special) * ss(0.35, 0.7, s.biome) * (slope < 0.2 ? 1 : 0) * 0.85,
    maxSlope: 0.2, sink: 0.03, tiltToNormal: 0, lod0: 130, range: 1000, wind: 0.035, castShadow: true,
    collider: { type: 'capsule', radius: 0.032, halfHeight: 0.36, y: 0.4 }, scannable: true, scanRadius: 0.16,
  },
  {
    id: 'ilex-chalk', body: 'ilex', name: 'Chalk spire',
    description: 'Wind-cut columns of soft white chalk, banded with grey. They crown the ridgelines of the highlands.',
    make: chalkSpire, roughness: 0.92, metalness: 0, hMin: 2, hMax: 7, candidates: 3,
    density: (s, slope) => (0.03 + 0.6 * s.rockiness * (1 - s.biome)) * (slope < 0.45 ? 1 : 0.3),
    maxSlope: 0.55, sink: 0.12, tiltToNormal: 0.4, lod0: 320, range: 1300, wind: 0, castShadow: true,
    collider: { type: 'capsule', radius: 0.3, halfHeight: 0.25, y: 0.5 }, scannable: true, scanRadius: 0.3,
  },
  {
    id: 'ilex-fan', body: 'ilex', name: 'Ochre fan-shrub',
    description: 'Low clumps of stiff, fan-shaped blades that catch the long light. Common on open ochre ground.',
    make: fanShrub, roughness: 0.85, metalness: 0, hMin: 0.6, hMax: 1.7, candidates: 12,
    density: (s, slope) => (0.3 + 0.25 * s.biome) * (1 - 0.8 * s.special) * (slope < 0.3 ? 1 : 0),
    maxSlope: 0.3, sink: 0.05, tiltToNormal: 0.7, lod0: 170, range: 170, wind: 0.08, castShadow: false,
    collider: null, scannable: true, scanRadius: 0.6,
  },
  // ----------------------------------------------------------- Vesper
  {
    id: 'vesper-glass', body: 'vesper', name: 'Black glass outcrop',
    description: 'Clusters of glossy black mineral crystals that push up through the dust. They ring faintly when the wind shifts.',
    make: blackGlass, roughness: 0.18, metalness: 0.35, hMin: 1, hMax: 3.6, candidates: 4,
    density: (s, slope) => (ss(0.3, 0.7, s.special) * 0.9 + 0.015) * (slope < 0.5 ? 1 : 0),
    maxSlope: 0.5, sink: 0.08, tiltToNormal: 0.5, lod0: 280, range: 1100, wind: 0, castShadow: true,
    collider: { type: 'ball', radius: 0.38, y: 0.32 }, scannable: true, scanRadius: 0.45,
  },
  {
    id: 'vesper-pillar', body: 'vesper', name: 'Rust hoodoo',
    description: 'Stacked drums of oxide-red sandstone under a darker cap rock, left standing as the mesas eroded around them.',
    make: rustPillar, roughness: 0.9, metalness: 0, hMin: 4, hMax: 11, candidates: 2,
    density: (s, slope) => 0.09 * (1 - s.biome) * (slope < 0.25 ? 1 : 0),
    maxSlope: 0.25, sink: 0.04, tiltToNormal: 0, lod0: 350, range: 1400, wind: 0, castShadow: true,
    collider: { type: 'capsule', radius: 0.18, halfHeight: 0.33, y: 0.48 }, scannable: true, scanRadius: 0.25,
  },
  {
    id: 'vesper-bristle', body: 'vesper', name: 'Dune bristle',
    description: 'Pale, wiry tufts that anchor the lee faces of the dunes. Their roots run far deeper than they stand tall.',
    make: duneBristle, roughness: 0.9, metalness: 0, hMin: 0.4, hMax: 1.0, candidates: 8,
    density: (s, slope) => 0.22 * s.biome * (slope < 0.35 ? 1 : 0),
    maxSlope: 0.35, sink: 0.05, tiltToNormal: 0.6, lod0: 130, range: 130, wind: 0.1, castShadow: false,
    collider: null, scannable: true, scanRadius: 0.6,
  },
  // ------------------------------------------------------------ Cairn
  {
    id: 'cairn-rime', body: 'cairn', name: 'Rime shard',
    description: 'Clusters of blue-white ice crystals grown in permanently shadowed crater floors. They glow faintly in the low sun.',
    make: rimeShard, roughness: 0.12, metalness: 0, emissive: 0x0a1a2e, hMin: 0.8, hMax: 2.6, candidates: 4,
    density: (s, slope) => ss(0.25, 0.65, s.special) * 0.7 * (slope < 0.4 ? 1 : 0),
    maxSlope: 0.4, sink: 0.06, tiltToNormal: 0.6, lod0: 240, range: 900, wind: 0, castShadow: true,
    collider: { type: 'ball', radius: 0.4, y: 0.3 }, scannable: true, scanRadius: 0.45,
  },
  {
    id: 'cairn-boulder', body: 'cairn', name: 'Silver breccia',
    description: 'Boulders of shock-fused rock fragments thrown out by ancient impacts, their faces glinting like hammered metal.',
    make: silverBoulder, roughness: 0.62, metalness: 0.25, hMin: 0.8, hMax: 4.2, candidates: 3,
    density: (s, slope) => (0.1 + 0.15 * (1 - s.biome)) * (slope < 0.5 ? 1 : 0.4),
    maxSlope: 0.6, sink: 0.15, tiltToNormal: 0.8, lod0: 300, range: 1000, wind: 0, castShadow: true,
    collider: { type: 'ball', radius: 0.5, y: 0.45 }, scannable: true, scanRadius: 0.5,
  },
  {
    id: 'cairn-pebbles', body: 'cairn', name: 'Ejecta pebbles',
    description: 'Scattered fragments of impact ejecta, sorted by nothing but chance.',
    make: pebbles, roughness: 0.8, metalness: 0.1, hMin: 1, hMax: 2, candidates: 6,
    density: (_s, slope) => 0.35 * (slope < 0.5 ? 1 : 0),
    maxSlope: 0.5, sink: 0.02, tiltToNormal: 1, lod0: 110, range: 110, wind: 0, castShadow: false,
    collider: null, scannable: false, scanRadius: 0.5,
  },
  // ------------------------------------------------------------- Earth
  // Scenery on land only (never under water or on snow), from the land-cover data:
  // trees where the cell is vegetated and forested, below the treeline; rocks in rough ground.
  {
    id: 'earth-conifer', body: 'earth', name: 'Needleleaf tree',
    description: 'A cone-shaped evergreen of the kind that dominates cool and mountain forests.',
    make: conifer, roughness: 0.85, metalness: 0, hMin: 9, hMax: 22, candidates: 10,
    density: (s, slope) => (s.liquidLevel != null ? 0 : earthForest(s) * (slope < 0.35 ? 0.55 : 0.2)),
    maxSlope: 0.55, sink: 0.02, tiltToNormal: 0, lod0: 220, range: 1200, wind: 0.012, castShadow: true,
    collider: { type: 'capsule', radius: 0.03, halfHeight: 0.3, y: 0.32 }, scannable: false, scanRadius: 0.2,
  },
  {
    id: 'earth-broadleaf', body: 'earth', name: 'Broadleaf tree',
    description: 'A round-crowned tree of the temperate and tropical forests.',
    make: broadleaf, roughness: 0.85, metalness: 0, hMin: 7, hMax: 18, candidates: 10,
    density: (s, slope) => (s.liquidLevel != null ? 0 : earthForest(s) * (slope < 0.3 ? 0.5 : 0.15)),
    maxSlope: 0.45, sink: 0.02, tiltToNormal: 0, lod0: 220, range: 1200, wind: 0.02, castShadow: true,
    collider: { type: 'capsule', radius: 0.04, halfHeight: 0.25, y: 0.3 }, scannable: false, scanRadius: 0.25,
  },
  {
    id: 'earth-boulder', body: 'earth', name: 'Boulder',
    description: 'A weathered block of bedrock.',
    make: earthBoulder, roughness: 0.75, metalness: 0, hMin: 0.8, hMax: 3.5, candidates: 4,
    density: (s, slope) => (s.liquidLevel != null ? 0 : (0.04 + 0.5 * ss(0.3, 0.8, s.rockiness)) * (slope < 0.6 ? 1 : 0.4)),
    maxSlope: 0.7, sink: 0.15, tiltToNormal: 0.8, lod0: 260, range: 900, wind: 0, castShadow: true,
    collider: { type: 'ball', radius: 0.5, y: 0.45 }, scannable: false, scanRadius: 0.5,
  },
  // -------------------------------------------------------------- Moon
  {
    id: 'moon-boulder', body: 'moon', name: 'Ejecta boulder',
    description: 'A block of lunar bedrock thrown out by an impact. The bright highland ones are anorthosite, made mostly of plagioclase feldspar; the dark ones on the maria are basalt.',
    make: lunarBoulder, roughness: 0.82, metalness: 0, hMin: 0.8, hMax: 4.5, candidates: 4,
    density: (s, slope) => (0.07 + 0.3 * ss(0.2, 0.6, s.rockiness)) * (slope < 0.5 ? 1 : 0.4),
    maxSlope: 0.6, sink: 0.15, tiltToNormal: 0.8, lod0: 300, range: 1000, wind: 0, castShadow: true,
    collider: { type: 'ball', radius: 0.5, y: 0.45 }, scannable: true, scanRadius: 0.5,
  },
  {
    id: 'moon-pebbles', body: 'moon', name: 'Regolith pebbles',
    description: 'Rock fragments in the lunar soil, broken by billions of years of impacts.',
    make: lunarPebbles, roughness: 0.9, metalness: 0, hMin: 1, hMax: 2, candidates: 6,
    density: (_s, slope) => 0.4 * (slope < 0.5 ? 1 : 0),
    maxSlope: 0.5, sink: 0.02, tiltToNormal: 1, lod0: 110, range: 110, wind: 0, castShadow: false,
    collider: null, scannable: false, scanRadius: 0.5,
  },
  // -------------------------------------------------------------- Mars
  {
    id: 'mars-basalt', body: 'mars', name: 'Vesicular basalt',
    description: 'Dark volcanic rock riddled with gas bubbles under a film of red dust, like the boulders the Spirit rover examined in Gusev crater.',
    make: marsBasalt, roughness: 0.8, metalness: 0, hMin: 0.7, hMax: 4, candidates: 4,
    density: (s, slope) => (0.08 + 0.3 * ss(0.2, 0.6, s.rockiness)) * (slope < 0.5 ? 1 : 0.4),
    maxSlope: 0.6, sink: 0.15, tiltToNormal: 0.8, lod0: 300, range: 1000, wind: 0, castShadow: true,
    collider: { type: 'ball', radius: 0.5, y: 0.45 }, scannable: true, scanRadius: 0.5,
  },
  {
    id: 'mars-pebbles', body: 'mars', name: 'Wind-sorted pebbles',
    description: 'Pebbles left behind where the wind has carried the fine dust away.',
    make: marsPebbles, roughness: 0.9, metalness: 0, hMin: 1, hMax: 2, candidates: 6,
    density: (s, slope) => 0.4 * (1 - s.special) * (slope < 0.5 ? 1 : 0),
    maxSlope: 0.5, sink: 0.02, tiltToNormal: 1, lod0: 110, range: 110, wind: 0, castShadow: false,
    collider: null, scannable: false, scanRadius: 0.5,
  },
];

export function speciesFor(body: BodyId): Species[] {
  return SPECIES.filter((s) => s.body === body);
}

export function speciesById(id: string): Species | undefined {
  return SPECIES.find((s) => s.id === id);
}
