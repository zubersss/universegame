// Per-world ambience data. Read from `BodyDef.ambience` (owned by ATLAS) when
// a body defines it; this table and a neutral default are the fallback so
// bodies without an entry still sound reasonable.

import { BODIES, type BodyId } from '../world/bodies';
import type { SurfaceInfo } from '../world/surface';

export type GroundKind = 'soil' | 'sand' | 'rock' | 'ice' | 'salt' | 'moss';

export interface AmbienceProfile {
  /** Wind loudness scale (0 = still air); multiplied by air density. */
  wind: number;
  /** Wind band centre in still air (Hz); rises with flow. */
  windTone: number;
  /** Tonal centre of the sparse ambient tones (Hz). */
  tonic: number;
  /** Scale of the ambient tones (semitones above the tonic). */
  scale: readonly number[];
  /** Timbre of the ambient tones. */
  timbre: OscillatorType;
  /** Mean seconds between ambient tones. */
  toneGap: number;
  /** Default ground under foot. */
  ground: GroundKind;
}

const PENTA = [0, 2, 4, 7, 9, 12, 14] as const;

export const DEFAULT_AMBIENCE: AmbienceProfile = {
  wind: 1, windTone: 300, tonic: 220, scale: PENTA, timbre: 'triangle', toneGap: 16, ground: 'soil',
};

const PROFILES: Partial<Record<BodyId, AmbienceProfile>> = {
  ilex: DEFAULT_AMBIENCE,
  vesper: { wind: 1, windTone: 300, tonic: 196, scale: PENTA, timbre: 'triangle', toneGap: 16, ground: 'sand' },
  cairn: { wind: 0, windTone: 300, tonic: 261.6, scale: PENTA, timbre: 'sine', toneGap: 16, ground: 'rock' },
};

/** `BodyDef.ambience` (ATLAS) when present, else the local table, else the default. */
export function ambienceFor(id: BodyId): AmbienceProfile {
  const def = (BODIES[id] as { ambience?: AmbienceProfile } | undefined)?.ambience;
  return def ?? PROFILES[id] ?? DEFAULT_AMBIENCE;
}

/** Airless bodies switch the on-foot mix to suit sounds. */
export function isAirless(id: BodyId): boolean {
  return BODIES[id].atmosphere === null;
}

/** Footstep timbre per ground: filter, cutoff (Hz), decay (s), level. */
export interface StepTimbre {
  filter: BiquadFilterType;
  cutoff: number;
  decay: number;
  level: number;
}

export const STEPS: Readonly<Record<GroundKind, StepTimbre>> = {
  soil: { filter: 'lowpass', cutoff: 900, decay: 0.07, level: 1 },
  sand: { filter: 'highpass', cutoff: 1800, decay: 0.11, level: 1 },
  rock: { filter: 'lowpass', cutoff: 500, decay: 0.07, level: 1 },
  ice: { filter: 'bandpass', cutoff: 2600, decay: 0.05, level: 0.8 },
  salt: { filter: 'highpass', cutoff: 2400, decay: 0.08, level: 0.9 },
  moss: { filter: 'lowpass', cutoff: 420, decay: 0.09, level: 0.8 },
};

/**
 * How the surface under the player changes the footstep, per body (data, not
 * branches): exposed rock above a rockiness threshold, a material where the
 * special mask is strong (ice, brine-wet salt, grove loam, valley mud), and a
 * material for biome B. Anything else uses the body's default ground.
 */
interface GroundRules {
  rock?: number;
  special?: { at: number; kind: GroundKind };
  biomeB?: { at: number; kind: GroundKind };
}

const GROUND_RULES: Partial<Record<BodyId, GroundRules>> = {
  ilex: { rock: 0.45, special: { at: 0.55, kind: 'moss' } },
  vesper: { biomeB: { at: 0.5, kind: 'sand' }, special: { at: 0.6, kind: 'rock' } },
  cairn: { special: { at: 0.4, kind: 'ice' } },
  orrin: { rock: 0.4, special: { at: 0.6, kind: 'soil' } },
  saro: { rock: 0.35, special: { at: 0.5, kind: 'ice' } },
};

/** Ground kind under foot from the surface info at the player's position. */
export function groundAt(id: BodyId, s: SurfaceInfo): GroundKind {
  const r = GROUND_RULES[id];
  const base = ambienceFor(id).ground;
  if (!r) return base;
  if (r.special && s.special >= r.special.at) return r.special.kind;
  if (r.rock !== undefined && s.rockiness >= r.rock) return 'rock';
  if (r.biomeB) return s.biome >= r.biomeB.at ? r.biomeB.kind : 'rock';
  return base;
}
