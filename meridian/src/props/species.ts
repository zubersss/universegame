import type { BodyId } from '../world/bodies';
import type { SurfaceInfo } from '../world/surface';
import {
  basaltOrgan, blackGlass, brineMat, chalkSpire, crustThorn, cushionMoss, duneBristle, fanShrub, fogReed, frostBloom, fulgurite, haliteRosette,
  lampCap, lanternTree, loamVesicle, pebbles, rimeShard, rustPillar, saltChimney, silverBoulder, sublimationVent,
  type SpeciesGeometry,
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
  // ------------------------------------------- appended (studio round)
  // Appended per body so existing species keep their per-body index (the
  // placement hash) and every existing prop keeps its ID and position.
  {
    id: 'ilex-vesicle', body: 'ilex', name: 'Loam vesicle',
    description: 'Clusters of thin-walled teal bladders rising from the loam in the deepest grove shade. They swell slowly through the day and slacken at dusk. Pressed, they yield a faint, sweet-smelling gas.',
    make: loamVesicle, roughness: 0.35, metalness: 0, emissive: 0x04110f, hMin: 0.25, hMax: 0.55, candidates: 6,
    density: (s, slope) => ss(0.55, 0.85, s.special) * ss(0.35, 0.7, s.biome) * 0.5 * (slope < 0.25 ? 1 : 0),
    maxSlope: 0.25, sink: 0.05, tiltToNormal: 0.8, lod0: 60, range: 120, wind: 0, castShadow: false,
    collider: null, scannable: true, scanRadius: 1.2,
  },
  {
    id: 'vesper-fulgurite', body: 'vesper', name: 'Fulgurite tube',
    description: 'Hollow, branching tubes of fused sand where lightning once struck the dunes. Their inner walls are glassy and smooth; the outer surface keeps the grain of the sand that formed them.',
    make: fulgurite, roughness: 0.45, metalness: 0.1, hMin: 0.5, hMax: 1.5, candidates: 2,
    density: (s, slope) => 0.05 * s.biome * (slope < 0.3 ? 1 : 0),
    maxSlope: 0.3, sink: 0.1, tiltToNormal: 0.3, lod0: 90, range: 260, wind: 0, castShadow: true,
    collider: null, scannable: true, scanRadius: 0.5,
  },
  {
    id: 'cairn-bloom', body: 'cairn', name: 'Frost bloom',
    description: 'Feathered hoar crystals that grow on rock faces the sun never reaches. Brought into light they sublimate within minutes; returned to shadow, they rebuild in the same shapes.',
    make: frostBloom, roughness: 0.2, metalness: 0, emissive: 0x08121e, hMin: 0.3, hMax: 1.0, candidates: 3,
    density: (s, slope) => (ss(0.15, 0.55, s.special) * 0.8 + 0.08) * ss(0.05, 0.22, slope),
    maxSlope: 0.6, sink: 0.05, tiltToNormal: 0.9, lod0: 90, range: 280, wind: 0, castShadow: false,
    collider: null, scannable: true, scanRadius: 0.6,
  },
  {
    id: 'cairn-vent', body: 'cairn', name: 'Sublimation vent',
    description: 'A fissure in the crater floor that releases a silent column of ice vapour each time the ice beneath it is warmed. The plume rises straight, without wind to bend it, and falls back as fine frost around the vent.',
    make: sublimationVent, roughness: 0.5, metalness: 0, hMin: 1.5, hMax: 3.5, candidates: 1,
    density: (s, slope) => 0.1 * ss(0.3, 0.7, s.special) * (slope < 0.15 ? 1 : 0),
    maxSlope: 0.15, sink: 0.01, tiltToNormal: 1, lod0: 150, range: 400, wind: 0, castShadow: false,
    collider: null, scannable: true, scanRadius: 0.4,
  },
  // ------------------------------------------------------------ Orrin
  {
    id: 'orrin-moss', body: 'orrin', name: 'Violet cushion-moss',
    description: 'Dense mounds of violet moss that carpet the lowlands, each cushion built from thousands of tightly packed shoots. The surface holds water like a sponge and gives slightly underfoot.',
    make: cushionMoss, roughness: 0.95, metalness: 0, hMin: 0.25, hMax: 0.6, candidates: 10,
    density: (s, slope) => 0.45 * ss(0.4, 0.8, s.biome) * (slope < 0.35 ? 1 : 0),
    maxSlope: 0.35, sink: 0.2, tiltToNormal: 0.9, lod0: 90, range: 160, wind: 0, castShadow: false,
    collider: null, scannable: true, scanRadius: 1.2,
  },
  {
    id: 'orrin-column', body: 'orrin', name: 'Basalt organ',
    description: 'Clusters of hexagonal basalt columns, split as an ancient lava sheet cooled and contracted. Wind crossing their tops produces a faint, steady tone.',
    make: basaltOrgan, roughness: 0.85, metalness: 0.05, hMin: 3, hMax: 10, candidates: 2,
    density: (s, slope) => (0.03 + 0.25 * s.rockiness) * (slope < 0.4 ? 1 : 0.3),
    maxSlope: 0.6, sink: 0.08, tiltToNormal: 0.2, lod0: 300, range: 1200, wind: 0, castShadow: true,
    collider: { type: 'capsule', radius: 0.3, halfHeight: 0.25, y: 0.5 }, scannable: true, scanRadius: 0.3,
  },
  {
    id: 'orrin-reed', body: 'orrin', name: 'Fog reed',
    description: 'Tall, hollow reeds that crowd the valley floors where the fog settles. Droplets condense along their stems and run down to the roots. In wind the stands give off a low hum.',
    make: fogReed, roughness: 0.8, metalness: 0, hMin: 2, hMax: 4, candidates: 8,
    density: (s, slope) => 0.5 * ss(0.3, 0.7, s.special) * (slope < 0.3 ? 1 : 0),
    maxSlope: 0.3, sink: 0.02, tiltToNormal: 0.3, lod0: 120, range: 300, wind: 0.05, castShadow: false,
    collider: null, scannable: true, scanRadius: 0.35,
  },
  {
    id: 'orrin-lampcap', body: 'orrin', name: 'Lamp cap',
    description: 'Stalked caps with a faint violet glow on their undersides, growing where the moss meets bare basalt. The glow is strongest in the fog and fades in clear air.',
    make: lampCap, roughness: 0.6, metalness: 0, emissive: 0x150a24, hMin: 0.4, hMax: 0.9, candidates: 3,
    density: (s, slope) => 0.35 * ss(0.2, 0.5, s.rockiness) * ss(0.2, 0.6, s.biome) * (slope < 0.35 ? 1 : 0) + 0.01,
    maxSlope: 0.35, sink: 0.03, tiltToNormal: 0.5, lod0: 80, range: 200, wind: 0, castShadow: false,
    collider: null, scannable: true, scanRadius: 0.8,
  },
  // ------------------------------------------------------------- Saro
  {
    id: 'saro-rosette', body: 'saro', name: 'Halite rosette',
    description: 'Clusters of pink cubic salt crystals grown where brine wicked up through the crust and evaporated. The colour comes from microbes trapped as the crystals formed.',
    make: haliteRosette, roughness: 0.3, metalness: 0, hMin: 0.2, hMax: 0.7, candidates: 6,
    density: (s, slope) => 0.25 * (1 - s.biome) * (slope < 0.4 ? 1 : 0),
    maxSlope: 0.4, sink: 0.1, tiltToNormal: 0.8, lod0: 90, range: 200, wind: 0, castShadow: false,
    collider: null, scannable: true, scanRadius: 0.8,
  },
  {
    id: 'saro-chimney', body: 'saro', name: 'Salt chimney',
    description: 'Hollow salt tubes that grow upward around brine seeps at the pan margins, ring by ring as the brine evaporates at the rim. Their lips stay wet and turquoise.',
    make: saltChimney, roughness: 0.6, metalness: 0, hMin: 1, hMax: 4, candidates: 2,
    density: (s, slope) => 0.3 * ss(0.2, 0.5, s.biome) * (1 - ss(0.6, 0.9, s.biome)) * (slope < 0.3 ? 1 : 0),
    maxSlope: 0.3, sink: 0.05, tiltToNormal: 0.1, lod0: 200, range: 700, wind: 0, castShadow: true,
    collider: { type: 'capsule', radius: 0.2, halfHeight: 0.3, y: 0.5 }, scannable: true, scanRadius: 0.3,
  },
  {
    id: 'saro-mat', body: 'saro', name: 'Brine mat',
    description: 'Flat, layered mats of microbes in the shallow brine, banded orange at the rim and crimson toward the centre. Each band is a different community living at a different salt concentration.',
    make: brineMat, roughness: 0.7, metalness: 0, hMin: 1, hMax: 3, candidates: 5,
    density: (s, slope) => 0.4 * ss(0.5, 0.9, s.biome) * (slope < 0.2 ? 1 : 0),
    maxSlope: 0.2, sink: 0, tiltToNormal: 1, lod0: 120, range: 260, wind: 0, castShadow: false,
    collider: null, scannable: true, scanRadius: 0.6,
  },
  {
    id: 'saro-thorn', body: 'saro', name: 'Crust thorn',
    description: 'Sparse, pale spikes that grow only along the cracks in the salt crust, where a little fresh water collects after dew. They excrete salt through their tips.',
    make: crustThorn, roughness: 0.8, metalness: 0, hMin: 0.3, hMax: 1, candidates: 8,
    density: (s, slope) => 0.15 * (1 - s.biome) * (slope < 0.35 ? 1 : 0),
    maxSlope: 0.35, sink: 0.05, tiltToNormal: 0.6, lod0: 110, range: 150, wind: 0.04, castShadow: false,
    collider: null, scannable: true, scanRadius: 0.7,
  },
];

export function speciesFor(body: BodyId): Species[] {
  return SPECIES.filter((s) => s.body === body);
}

export function speciesById(id: string): Species | undefined {
  return SPECIES.find((s) => s.id === id);
}
